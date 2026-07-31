# Querying the Surveillance KG

Ways to ask the graph questions, once it's loaded into the `surveillance` tenant on a running engine
(see [GETTING_STARTED.md](../GETTING_STARTED.md)). The HTTP and MCP examples below were run live and
return real results.

---

## 1. Claude, over MCP (natural language)

This repo doesn't ship a bespoke MCP server, but the `samyama` package includes a generic one that can
serve any tenant:

```bash
# point Claude Code at the running engine's `surveillance` tenant:
claude mcp add surveillance -- samyama-mcp-serve --url http://localhost:8080 --graph surveillance

# start a new Claude Code session (MCP servers load at session start), then just ask:
#   "which diseases are reported most often?"     → Tuberculosis incidence, dengue fever, ...
#   "how many countries are in the graph?"
```

(`samyama-mcp-serve --list-tools --url http://localhost:8080 --graph surveillance` prints the tools it
auto-generates from the schema.)

## 2. HTTP API (`POST /api/query`) — recommended

```bash
curl -s -X POST http://localhost:8080/api/query -H 'Content-Type: application/json' -d '{
  "graph": "surveillance",
  "query": "MATCH (c:Country)-[:REPORTED]->(r:DiseaseReport)-[:REPORT_OF]->(d:Disease) RETURN d.name AS disease, count(r) AS reports ORDER BY reports DESC LIMIT 3"
}'
```
```json
{"columns":["disease","reports"],
 "records":[["Tuberculosis incidence (per 100 000 population)",788],
            ["TB deaths (excluding HIV+TB)",708],
            ["Reported cases of dengue fever",683]]}
```

## 3. Samyama CLI (Redis wire protocol, `:6379`)

The engine also speaks the Redis wire protocol:

```bash
redis-cli -p 6379 GRAPH.QUERY surveillance \
  "MATCH (c:Country)-[:REPORTED]->(r:DiseaseReport)-[:REPORT_OF]->(d:Disease) RETURN d.name, count(r) AS reports ORDER BY reports DESC LIMIT 3"
```

> **Note:** on the current engine build the RESP/`GRAPH.QUERY` path returns empty results for some
> queries on this tenant that the HTTP API answers correctly (tracked upstream in
> [samyama-graph](https://github.com/samyama-ai/samyama-graph)). Until that's fixed, prefer the **HTTP
> API** or **MCP** for the surveillance KG.

---

## More queries
See **[schema/surveillance_kg.cypher](../schema/surveillance_kg.cypher)** for the full node/edge model.
