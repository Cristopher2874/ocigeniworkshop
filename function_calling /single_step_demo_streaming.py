#!/Users/ashish/anaconda3/bin/python
# Questions use #generative-ai-users  or #igiu-innovation-lab slack channel
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import OnDemandServingMode, EmbedTextDetails,CohereChatRequest, ChatDetails
import oci
import json

#####
#Setup
#Change the compartmentid to yhe ocid of your compartment
#Change the profile if needed
#####

CONFIG_PROFILE = "AISANDBOX"
compartmentId= "ocid1.compartment.oc1..aaaaaaaaxj6fuodcmai6n6z5yyqif6a36ewfmmovn42red37ml3wxlehjmga" 
llm_service_endpoint= "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)

llm_client = GenerativeAiInferenceClient(
                config=config,
                service_endpoint=llm_service_endpoint,
                retry_strategy=oci.retry.NoneRetryStrategy(),
                timeout=(10,240))


item_param = oci.generative_ai_inference.models.CohereParameterDefinition()
item_param.description = "the item requested to be purchased, in all caps eg. Bananas should be BANANAS"
item_param.type = "str"
item_param.is_required = True

quantity_param = oci.generative_ai_inference.models.CohereParameterDefinition()
quantity_param.description = "how many of the items should be purchased"
quantity_param.type = "int"
quantity_param.is_required = True

shop_tool = oci.generative_ai_inference.models.CohereTool()
shop_tool.name = "personal_shopper"
shop_tool.description = "Returns items and requested volumes to purchase"
shop_tool.parameter_definitions = {
    "item": item_param,
    "quantity": quantity_param
}

# Step 1, describe the tool spec

chat_request = oci.generative_ai_inference.models.CohereChatRequest()
chat_request.message = "I'd like 4 apples and a fish please"
chat_request.max_tokens = 600
chat_request.is_stream = True
chat_request.is_force_single_step = True
chat_request.tools = [ shop_tool ]

chat_detail = oci.generative_ai_inference.models.ChatDetails()
chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id="cohere.command-r-08-2024")
chat_detail.compartment_id = compartmentId
chat_detail.chat_request = chat_request

chat_response = llm_client.chat(chat_detail)

# Print result
print("**************************Step 1 Result**************************")
#print(vars(chat_response))

def get_tool_calls(chat_response):
    for event in chat_response.data.events():
        res = json.loads(event.data)
        if 'finishReason' in res:
            print(f"\ntools to call: {res['toolCalls']}")
            return res['toolCalls']
        if 'text' in res:
            print(res['text'], end="", flush=True)
    print("\n")
    return None

tool_calls = get_tool_calls(chat_response)

# Step 2, provide the tool results and get the final response

chat_request.tool_results = []
for call in tool_calls:
    tool_result = oci.generative_ai_inference.models.CohereToolResult()
    tool_result.call = call
    tool_result.outputs = [ { "response": "Completed" } ] 
    chat_request.tool_results.append(tool_result)

chat_response = llm_client.chat(chat_detail)

# Print result
print("**************************Step 2 Result**************************")
#print(vars(chat_response))

for event in chat_response.data.events():
    res = json.loads(event.data)
    if 'finishReason' in res:
        print(f"\nFinish reason: {res['finishReason']}")
        break
    if 'text' in res:
        print(res['text'], end="", flush=True)
print("\n")