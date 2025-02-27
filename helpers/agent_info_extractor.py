class AgentInfoExtractor:
    def __init__(self, bedrock_agent_client):
        self.client = bedrock_agent_client

    def get_agent_alias_version(self, agent_id, alias_id):
        """Get agent version from alias information"""
        alias_info = self.client.get_agent_alias(agentAliasId=alias_id, agentId=agent_id)
        return alias_info['agentAlias']['routingConfiguration'][0]['agentVersion']
    
    def get_agent_name(self, agent_id):
        """Get agent name from agent information"""
        agent_info = self.client.get_agent(agentId=agent_id)
        return agent_info['agent']['agentName']

    def get_agent_version_details(self, agent_id, agent_version):
        """Get detailed information about an agent version"""
        version_info = self.client.get_agent_version(agentId=agent_id, agentVersion=agent_version)


        #LOGIC FOR CHANGING THE MODEL NAME IN CASE OF USING CROSS-REGION REFERENCE
        model_id = version_info['agentVersion']['foundationModel'].split('/')[-1]
        if model_id.startswith("us."):
            # print("Changing model name from cross-region reference")
            model_id = model_id[3:]

        
        return {
            'model_id': model_id,
            'instruction': version_info['agentVersion']['instruction'],
            'description': version_info['agentVersion']['description']
        }

    def get_action_groups(self, agent_id, agent_version):
        """Get action groups for an agent"""
        return self.client.list_agent_action_groups(
            agentId=agent_id,
            agentVersion=agent_version
        )['actionGroupSummaries']

    def create_agent_info(self, agent_id, alias_id, agent_type):
        """Create a standardized agent info dictionary"""
        agent_name = self.get_agent_name(agent_id)
        agent_version = self.get_agent_alias_version(agent_id, alias_id)
        version_details = self.get_agent_version_details(agent_id, agent_version)
        action_groups = self.get_action_groups(agent_id, agent_version)

        
        # Agent info in a dictionary
        agent_info = {
            "agentId": agent_id,
            "agentAlias": alias_id,
            "agentName": agent_name,
            "agentVersion": agent_version,
            "agentType": agent_type,
            "agentModel": version_details['model_id'],
            "agentDescription": version_details['description'],
            "agentInstruction": version_details['instruction'],
            "actionGroups": action_groups
        }
        
        # print("Agent info: {}".format(agent_info))

        return agent_info

    def get_collaborator_info(self, agent_id, agent_version):
        """Get information about collaborator agents"""

        # Get whole list of collaborators
        collaborators = self.client.list_agent_collaborators(
            agentId=agent_id, 
            agentVersion=agent_version
        )['agentCollaboratorSummaries']

        #new dictionary of collaborator info consisting of: name, description, instruction
        collaborator_info = {}
        for collab in collaborators:
            
            # Create dictionary with specific collaborator's info
            collab_info = {
                # "collaboratorAgentId": collab['agentDescriptor']['aliasArn'].split('/')[-2],
                # "collaboratorAlias": collab['agentDescriptor']['aliasArn'].split('/')[-1],
                # "collaboratorId": collab['collaboratorId'],
                "collaborationInstruction": collab['collaborationInstruction'],
            }

            # Use collab_name as key
            collaborator_info[collab['collaboratorName']] = collab_info

            
        # print(collaborator_info)

        return collaborator_info

    def extract_agent_info(self, agent_id, agent_alias_id):
        """Main method to extract all agent information"""
        agents_info = {}
        
        # Check if agent is collaborative
        is_collaborative = self.client.get_agent(
            agentId=agent_id
        )['agent']['agentCollaboration'] != "DISABLED"

        # Add main agent info
        agent_type = "MULTI-AGENT" if is_collaborative else "SINGLE-AGENT"
        
        # Create agent_info dictionary
        agents_info = self.create_agent_info(agent_id, agent_alias_id, agent_type)

        # Add collaborator info if collaborative
        if is_collaborative:
            agent_version = self.get_agent_alias_version(agent_id, agent_alias_id)

            # Create new key called 'collaborators'
            agents_info['collaborators'] = self.get_collaborator_info(agent_id, agent_version)
        
        else:
            # Create new key called 'collaborators'
            agents_info['collaborators'] = None

        return agents_info