from django.http import HttpResponse
from django.template import loader
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from django.shortcuts import render
import os
from django.conf import settings
import os
from django.conf import settings


def mgjfrontend(request):
  template = loader.get_template('homepage.html')
  return HttpResponse(template.render())

def mgjfrontend(request):
    output_text = None
    notebook_path = os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'mw-tester.ipynb'))

    if request.method == "POST":
        input_text = request.POST.get("input_text")
        option1 = "option1" in request.POST
        option2 = "option2" in request.POST

        # Load the notebook
        with open(notebook_path) as f:
            nb = nbformat.read(f, as_version=4)

        # Inject variables at the start of the notebook
        param_code = f"""
          input_text = "{input_text}"
          Podcast = {option1}
          YouTube = {option2}
          """
        nb.cells.insert(0, nbformat.v4.new_code_cell(param_code))

        # Execute it
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
        ep.preprocess(nb, {'metadata': {'path': '.'}})

        # Extract output from last code cell
        for cell in nb.cells[::-1]:
            if cell.cell_type == 'code' and cell.outputs:
                for out in cell.outputs:
                    if 'text' in out:
                        output_text = out['text']
                        break
                if output_text:
                    break

    return render(request, "homepage.html", {"output": output_text})

