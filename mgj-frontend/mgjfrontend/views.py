from django.shortcuts import render
import os
from django.conf import settings
import sys

sys.path.append(os.path.abspath(os.path.join(settings.BASE_DIR, '..')))
from main import planner, run_RAI, format_plan_steps


def mgjfrontend(request):
    plan_steps = None
    formatted_steps = None
    final_output = None
    constraints = []
    topic = ""
    further_reading = False
    youtube_videos = False
    notion_redirect = None
    quiz = False

    if request.method == "POST":
        action = request.POST.get("action")
        print(action)

        if action == "generate":

            topic = request.POST.get("topic", "")
            further_reading = request.POST.get("further_reading") == "on"
            youtube_videos = request.POST.get("youtube_videos") =="on"
            quiz = request.POST.get("quiz") == "on"

            constraints = []
            plan, plan_steps, task_fn, portia = planner(topic, constraints, further_reading, youtube_videos, quiz)

            request.session["topic"] = topic
            request.session["youtube_videos"] = youtube_videos
            request.session["further_reading"] = further_reading
            request.session["constraints"] = constraints
            request.session["quiz"] = quiz

            request.session["task_text"] = task_fn()
            request.session["plan_steps"] = plan_steps

            print("quiz", quiz)
            print("youtube", youtube_videos)
            print("further_reading", further_reading)

            formatted_steps = format_plan_steps(plan_steps)

        elif action == "clear":
            request.session.flush()
            return render(request, "homepage.html")

        elif action == "feedback":
            decision = request.POST.get("decision")
            additional = request.POST.get("additional_guidance", "").strip()

            topic = request.session.get("topic")
            youtube_videos = request.session.get("youtube_videos", False)
            further_reading = request.session.get("further_reading", False)
            quiz = request.session.get("quiz", False)
            constraints = request.session.get("constraints", [])

            print("ACTION", request.POST.get("action"))
            print("DECISION", request.POST.get("decision"))
            print("GUIDANCE", request.POST.get("additional_guidance"))

            if decision == "no":
                if additional:
                    constraints.append(additional)
                    request.session["constraints"] = constraints

                plan, plan_steps, task_fn, portia = planner(topic, constraints, youtube_videos, further_reading, quiz)
                request.session["task_text"] = task_fn()
                request.session["plan_steps"] = plan_steps
                formatted_steps = format_plan_steps(plan_steps)

            elif decision == "yes":
                task_text = request.session.get("task_text")
                task_fn = lambda: task_text

                final_output = run_RAI(task_fn=task_fn)

                if isinstance(final_output, dict) and final_output.get("clarification_required"):
                    return render(request, "homepage.html", {
                        "clarification_required": True,
                        "clarification_message": final_output["message"],
                        "plan_run_id": final_output["plan_run_id"],
                        "argument_name": final_output["argument_name"],
                        "topic": topic,
                        "plan_steps": format_plan_steps(request.session.get("plan_steps", [])),
                    })
                

         
        elif action == "clarify":
            clarification_response = request.POST.get("clarification_response")
            argument_name = request.POST.get("argument_name")
            plan_run_id = request.POST.get("plan_run_id")
            task_text = request.session.get("task_text")
            task_fn = lambda: task_text

            final_output = run_RAI(
                task_fn = task_fn,
                clarification_response=clarification_response,
                clarification_context={
                    "argument_name": argument_name,
                    "plan_run_id": plan_run_id
                }
            )
            print(final_output)


    if not formatted_steps and "plan_steps" in request.session:
        formatted_steps = format_plan_steps(request.session["plan_steps"])

    output = None
    

    if isinstance(final_output, dict):
        output = final_output.get("output")
        notion_redirect = final_output.get("notion_parent_id") if (
            output == "Your plan has executed successfully!"
        ) else None
    elif final_output:
        output = final_output

    return render(request, "homepage.html", {
        "topic": topic,
        "plan_steps": formatted_steps or request.session.get("plan_steps"),
        "output": output,
        "notion_redirect": notion_redirect
    })
