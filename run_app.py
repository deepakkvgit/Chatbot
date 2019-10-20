from rasa_core.channels import HttpInputChannel
from rasa_core.agent import Agent
from rasa_core.interpreter import RasaNLUInterpreter
from rasa_slack_connector import SlackInput


nlu_interpreter = RasaNLUInterpreter('./models/nlu/default/restaurantnlu')
agent = Agent.load('./models/dialogue', interpreter = nlu_interpreter)

input_channel = SlackInput('xoxp-623102633093-625916629409-795261422928-66314fc52c7bff2ac25ce248931e2a84', #app verification token
							'xoxb-623102633093-797468902166-9nm19txSzlu4ape3en98AtvV', # bot verification token
							'KzsHtMlb1CypfIjMdpJRUz22', # slack verification token
							True)

agent.handle_channel(HttpInputChannel(5004, '/', input_channel))