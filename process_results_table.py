import json
import os

with open('summary.json') as f:
    data = json.load(f)
#print(models_all)
#print(platforms)

tableposhtml = """
<!-- pager -->
<div class="pager PAGER_CLASS">
            <img src="https://mottie.github.io/tablesorter/addons/pager/icons/first.png" class="first"/>
            <img src="https://mottie.github.io/tablesorter/addons/pager/icons/prev.png" class="prev"/>
            <span class="pagedisplay"></span> <!-- this can be any element, including an input -->
            <img src="https://mottie.github.io/tablesorter/addons/pager/icons/next.png" class="next"/>
            <img src="https://mottie.github.io/tablesorter/addons/pager/icons/last.png" class="last"/>
            <select class="pagesize" title="Select page size">
            <option selected="selected" value="10">10</option>
            <option value="20">20</option>
            <option value="30">30</option>
            <option value="all">All</option>
            </select>
            <select class="gotoPage" title="Select page number"></select>
</div>
        """

def get_json_files(github_url):
    import requests
    from bs4 import BeautifulSoup

    retries = 5
    retry_delay = 2

    for attempt in range(retries):
        try:
            # Get the content of the GitHub page
            response = requests.get(github_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all JSON files
            #print(soup)
            # Find the <script> tag with the specific data-target attribute
            script_tag = soup.find('script', {'data-target': 'react-app.embeddedData', 'type': 'application/json'})

            if script_tag:
                # Extract the JSON content from the script tag
                json_data = script_tag.string

                # Parse the JSON string into a Python dictionary
                data = json.loads(json_data)

                # Access the parts of the JSON you are interested in
                tree_items = data.get('payload', {}).get('tree', {}).get('items', [])
                
                json_files = [a['name'] for a in tree_items if a['name'].endswith('.json')]

                return json_files
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:  # Don't wait after the last attempt
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Exiting.")
                return None

def find_match(files, re_name):
    import re 
    for file in files:
        if re.match(re_name, file):
            return file
    print(re_name)
    print(files)
    return None


def getsummarydata(data, category, division):
    mydata = {}
    mycountdata = {}
    for item in data:
        if item['Suite'] != category:
            continue
        if item['Category'] != division:
            continue
        '''
        if item['Availability'] != availability:
            continue
        '''
        submitter = item['Submitter']
        if mydata.get(submitter, '') == '':
            mydata[submitter] = {}
        myid = item['ID']
        if mydata[submitter].get(myid, '') == '':
            mydata[submitter][myid] = {}
        model = item['Model']
        if mydata[submitter][myid].get(model, '') == '':
            mydata[submitter][myid][model] = {}
            mydata[submitter][myid][model]['count'] = 0
        if division == "open":
            scenario = item['Scenario']
            if mydata[submitter][myid][model].get(scenario, '') == '':
                mydata[submitter][myid][model][scenario] = 0

        mydata[submitter][myid][model]['count'] += 1

    #print(mydata)
    for submitter,value in mydata.items():
        mycountdata[submitter] = {}
        for sut, results in value.items():
            for model, model_data in results.items():
                if mycountdata[submitter].get(model, '') == '':
                    mycountdata[submitter][model] = 0
                mycountdata[submitter][model] += model_data['count']
    return mydata, mycountdata









def processdata(data, category, division, availability):

    mydata = {}
    needed_keys_model = [ "has_power", "Performance_Result", "Performance_Units", "Accuracy", "Location" ]

    needed_keys_system = [ "System", "Submitter", "Availability", "Category", "Accelerator", "a#", "Nodes", "Processor", "host_processors_per_node", "host_processor_core_count", "Notes", "Software", "Details", "Platform" ]
    for item in data:
        if item['Suite'] != category:
            continue
        if item['Category'] != division:
            continue
        if item['Availability'] != availability:
            continue
        myid = item['ID']
        if mydata.get(myid, '') == '':
            mydata[myid] = {}
        model = item['Model']
        if mydata[myid].get(model, '') == '':
            mydata[myid][model] = {}
        scenario = item['Scenario']
        if mydata[myid][model].get(scenario, '') == '':
            mydata[myid][model][scenario] = {}

        mydata[myid][model][scenario]['has_power'] = item['has_power']
        if item['has_power'] and item.get('Power_Result'):
            mydata[myid][model][scenario]['Power_Result'] = item['Power_Result']
            mydata[myid][model][scenario]['Power_Units'] = item['Power_Units']
        for key in needed_keys_model:
            mydata[myid][model][scenario][key] = item[key]
        for key in needed_keys_system:
            mydata[myid][key] = item[key]
    return mydata

models = [ "llama2-70b-99", "llama2-70b-99.9", "gptj-99", "gptj-99.9", "bert-99", "bert-99.9", "stable-diffusion-xl",  "dlrm-v2-99", "dlrm-v2-99.9", "retinanet", "resnet", "3d-unet-99", "3d-unet-99.9"  ]

def get_precision_info(measurements_url, platform):
    github_url  = measurements_url
    measurements_json_file_name =  find_match(get_json_files(github_url), f"""^{platform}.*\\.json$""")
    measurements_json = f"""{github_url}{measurements_json_file_name}"""
    measurements_json_raw = measurements_json.replace("github.com", "raw.githubusercontent.com").replace("/tree/", "/")
    import urllib.request
    with urllib.request.urlopen(measurements_json_raw) as url:
        data = json.load(url)
    return data

def construct_table(category, division, availability):
    # Initialize the HTML table with the header
    html = f"""<div id="results_table_{availability}" class="resultstable_wrapper"> <table class="resultstable tablesorter" id="results_{availability}">"""
    html += "<thead> <tr>"
    
    # Table header
    tableheader = f"""
        <th id="col-id" class="headcol col-id">ID</th>
        <th id="col-system" class="headcol col-system">System</th>
        <th id="col-submitter" class="headcol col-submitter">Submitter</th>
        <th id="col-accelerator" class="headcol col-accelerator">Accelerator</th>
        <th id="col-llama2-99" colspan="2">LLAMA2-70B-99</th>
        <th id="col-llama2-99.9" colspan="2">LLAMA2-70B-99.9</th>
        <th id="col-gptj-99" colspan="2">GPTJ-99</th>
        <th id="col-gptj-99.9" colspan="2">GPTJ-99.9</th>
        <th id="col-bert-99" colspan="2">Bert-99</th>
        <th id="col-bert-99.9" colspan="2">Bert-99.9</th>
        <th id="col-dlrm-v2-99" colspan="2">Stable Diffusion</th>
        <th id="col-dlrm-v2-99" colspan="2">DLRM-v2-99</th>
        <th id="col-dlrm-v2-99.9" colspan="2">DLRM-v2-99.9</th>
        <th id="col-retinanet" colspan="2">Retinanet</th>
        <th id="col-resnet50" colspan="2">ResNet50</th>
        <th id="col-3d-unet-99" colspan="1">3d-unet-99</th>
        <th id="col-3d-unet-99.9" colspan="1">3d-unet-99.9</th>
        """ 
    tableheader += "</tr>"
    
    tableheader += f"""
    <tr>
    <th class="headcol col-id"></th>
    <th class="headcol col-system"></th>
    <th class="headcol col-submitter"></th>
    <th class="headcol col-accelerator"></th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Server</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Offline</th>
    <th class="col-scenario">Offline</th>
    """
    
    
    # Add header and footer
    html += tableheader
    html += "</tr></thead>"
    html += f"<tfoot> <tr>{tableheader}</tr></tfoot>"

    mydata = processdata(data, category, division, availability)

    if not mydata:
        return None

    #models = [ "resnet", "retinanet", "bert-99", "bert-99.9", "gptj-99", "gptj-99.9", "llama2-70b-99", "llama2-70b-99.9", "stable-diffusion-xl", "dlrm-v2-99", "dlrm-v2-99.9", "3d-unet-99", "3d-unet-99.9"  ]


    location_pre = "https://github.com/mlcommons/inference_results_v4.0/tree/main/"
    result_link_text = "See result logs"
    result_link_text = ""
    for rid in mydata:
        extra_sys_info = f"""
Processor: {mydata[rid]['Processor']}
Software: {mydata[rid]['Software']}
Cores per processor: {mydata[rid]['host_processor_core_count']}
Processors per node: {mydata[rid]['host_processors_per_node']}
Nodes: {mydata[rid]['Nodes']}
Notes: {mydata[rid]['Notes']}
        """
        a_num = mydata[rid]['a#']
        if a_num =='':
            acc = ""
        else:
            acc = f"{mydata[rid]['Accelerator']} x {int(a_num)}"
        system_json_link = f"""{mydata[rid]['Details'].replace("results", "systems").replace("submissions_inference_4.0", "inference_results_v4.0")}.json"""
        html += f"""
        <tr>
        <td class="col-id headcol"> {rid} </td>
        <td class="col-system headcol" title="{extra_sys_info}"> <a target="_blank" href="{system_json_link}"> {mydata[rid]['System']} </a> </td>
        <td class="col-submitter headcol"> {mydata[rid]['Submitter']} </td>
        <td class="col-accelerator headcol"> {acc} </td>
        """
        for m in models:
            if mydata[rid].get(m):
                if mydata[rid][m].get('Server'):
                    github_server_url  = f"""{location_pre}{mydata[rid][m]['Server']['Location'].replace("results", "measurements")}/"""
                    server_precision_info = get_precision_info( github_server_url, mydata[rid]['Platform'])
                    extra_model_info = f"""Weight data types: {server_precision_info['weight_data_types']}
Input data types: {server_precision_info['input_data_types']}
                    """
                    #print(server_precision_info)
                    
                    html += f"""
                        <td class="col-result"><a target="_blank" title="{result_link_text}{extra_model_info}" href="{location_pre}{mydata[rid][m]['Offline']['Location']}"> {round(mydata[rid][m]['Server']['Performance_Result'],1)} </a> </td>
                    """
                github_offline_url  = f"""{location_pre}{mydata[rid][m]['Offline']['Location'].replace("results", "measurements")}/"""
                offline_precision_info = get_precision_info( github_offline_url, mydata[rid]['Platform'])
                extra_model_info = f"""Weight data types: {offline_precision_info['weight_data_types']}
Input data types: {offline_precision_info['input_data_types']}
                    """
                html += f"""
                <td class="col-result"><a target="_blank" title="{result_link_text}{extra_model_info}" href="{location_pre}{mydata[rid][m]['Offline']['Location']}"> {round(mydata[rid][m]['Offline']['Performance_Result'],1)} </a> </td>
                """
            else:
                html += f"""
                <td></td>
                """
                if "3d-unet" not in m:
                    html += f"""
                    <td></td>
                    """


        html += f"""
        </tr>
        """
    
    html += "</table></div>"
    
    return html


def construct_summary_table(category, division):
    summary_data, count_data = getsummarydata(data, category, division)
    #print(count_data)

    html  = ""
    html += """
    <div class="counttable_wrapper">
    <table class="tablesorter counttable">
    <thead>
    <tr>
    <th class="count-submitter">Submitter</th>
        <th id="col-llama2-99">LLAMA2-70B-99</th>
        <th id="col-llama2-99.9">LLAMA2-70B-99.9</th>
        <th id="col-gptj-99">GPTJ-99</th>
        <th id="col-gptj-99.9">GPTJ-99.9</th>
        <th id="col-bert-99">Bert-99</th>
        <th id="col-bert-99.9">Bert-99.9</th>
        <th id="col-dlrm-v2-99">Stable Diffusion</th>
        <th id="col-dlrm-v2-99">DLRM-v2-99</th>
        <th id="col-dlrm-v2-99.9">DLRM-v2-99.9</th>
        <th id="col-retinanet">Retinanet</th>
        <th id="col-resnet50">ResNet50</th>
        <th id="col-3d-unet-99">3d-unet-99</th>
        <th id="col-3d-unet-99.9">3d-unet-99.9</th>
        <th id="all-models">Total</th>
        </tr>
        </thead>
        """
    total_counts = {}
    for submitter, item in count_data.items():
        html += "<tr>"
        cnt = 0

        html += f"""<td class="count-submitter"> {submitter} </td>"""
        for m in models:
            if item.get(m, '') != '':
                html += f"""<td class="col-result"> {item[m]} </td>"""
                cnt += item[m]
                if total_counts.get(m, '') == '':
                    total_counts[m] = item[m]
                else:
                    total_counts[m] += item[m]
            else:
                html += f"""<td class="col-result"> 0 </td>"""
        html += f"""<td class="col-result"> {cnt} </td>"""
        html += "</tr>"
    html += """
    <tr>
    <td class="count-submitter">Total</td>
    """
    total = 0
    for m in models:
        if total_counts.get(m, '') != '':
            html += f"""<td class="col-result"> {total_counts[m]} </td>"""
            total += total_counts[m]
        else:
            html += f"""<td class="col-result"> 0 </td>"""
    html += f"""<td class="col-result"> {total} </td>"""
    html += "</tr>"

    html += "</table></div>"
    return html









categories = { "datacenter" : "Datacenter",
              "edge": "Edge"
              }
divisions= {
        "closed": "Closed",
        "open": "Open"
        }

availabilities = ["Available", "Preview", "RDI" ]
#availabilities = ["Available" ]
division="closed"
category="datacenter"
html = ""
for availability in availabilities:
    val = availability.lower()
    pager_class= f"pager_{val}"
    tableposhtmlval = tableposhtml.replace("PAGER_CLASS", pager_class)
    html_table = construct_table(category, division, val)

    if html_table:
        html += f"""
        <h2>{categories[category]} Category: {availability} submissions in {divisions[division]} division</h2>
{tableposhtmlval}
{html_table}
{tableposhtmlval}
<hr>
"""
summary = construct_summary_table(category, division)
#print(summary)
html += f"""
<h2>Count of Results </h2>
{summary}
<hr>
"""


extra_scripts = """
<script type="text/javascript">
var sortcolumnindex = 4, perfsortorder = 1;
</script>

<script type="text/javascript" src="javascripts/results_tablesorter.js"></script>

"""

out_html = f"""---
hide:
  - navigation
  - toc
---

<html>
{html}
{extra_scripts}
</html>
"""
with open(os.path.join("docs", "index.md"), "w") as f:
    f.write(out_html)


#print(data)
def generate_html_form(platforms, models_all, data1=None, data2=None, modelsdata=None):
    # Setting default values if not provided
    if not data1:
        data1 = ''
    if not data2:
        data2 = ''
    if not modelsdata:
        modelsdata = 'All models'

    # Create select options for system 1 and system 2
    def generate_select_options(options, selected_value):
        html = ""
        for key, value in options.items():
            selected = 'selected' if key == selected_value else ''
            html += f"<option value='{key}' {selected}>{value}</option>\n"
        return html

    system1_options = generate_select_options(platforms, data1)
    system2_options = generate_select_options(platforms, data2)

    # Create select options for models
    models_options = generate_select_options(models_all, modelsdata)

    # Generate the HTML for the form
    html_form = f"""
    <form id="compareform"  method="post" action="">
        <h3>Compare Results</h3>

        <div class="form-field">
            <label for="system1">System 1</label>
            <select id="system1" name="system1" class="col">
                {system1_options}
            </select>
        </div>

        <div class="form-field">
            <label for="system2">System 2</label>
            <select id="system2" name="system2" class="col">
                {system2_options}
            </select>
        </div>

        <div class="form-field">
            <label for="models">Models</label>
            <select id="models" name="models[]" class="col" multiple>
                {models_options}
            </select>
        </div>

        <div class="form-field">
            <button type="submit" name="okthen" value="1" id="compare_results">Compare SUTs</button>
        </div>
    </form>
    """

    return html_form

