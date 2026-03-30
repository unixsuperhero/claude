Re-authenticate all mcp-usher servers in parallel by opening browser tabs for each one.

\`\`\`bash
for id in $(curl -s localhost:15245/api/servers | python3 -c "import sys,json; [print(s['id']) for s in json.load(sys.stdin)]"); do curl -sX POST localhost:15245/api/servers/$id/reauth >/dev/null; done
\`\`\`