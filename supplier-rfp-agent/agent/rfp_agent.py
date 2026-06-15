from strands import Agent
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.supplier_lookup_tool  import supplier_lookup_tool
from tools.rfp_generator_tool    import rfp_generator_tool
from tools.email_dispatch_tool   import email_dispatch_tool
from tools.proposal_fetch_tool   import proposal_fetch_tool
from tools.scoring_tool          import scoring_tool
from tools.recommendation_tool   import recommendation_tool
from agent.system_prompt         import SYSTEM_PROMPT
from config                      import BEDROCK_MODEL_ID

rfp_agent = Agent(
    model=BEDROCK_MODEL_ID,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        supplier_lookup_tool,
        rfp_generator_tool,
        email_dispatch_tool,
        proposal_fetch_tool,
        scoring_tool,
        recommendation_tool,
    ],
)
