from tools import shodan, neo4j, filesystem

tools = []
tools.extend(shodan.register())
tools.extend(neo4j.register())
tools.extend(filesystem.register())

app = MCPServer(tools=tools)