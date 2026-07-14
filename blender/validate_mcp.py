import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    servidor = StdioServerParameters(
        command="/opt/homebrew/bin/uv",
        args=[
            "--directory",
            "/Users/huiosweb/.local/share/blender-mcp-official/mcp",
            "run",
            "blender-mcp",
        ],
    )

    async with stdio_client(servidor) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            inicializacao = await sessao.initialize()
            ferramentas = await sessao.list_tools()
            nomes = [ferramenta.name for ferramenta in ferramentas.tools]
            print(f"SERVIDOR={inicializacao.serverInfo.name}")
            print(f"VERSAO={inicializacao.serverInfo.version}")
            print(f"FERRAMENTAS={len(nomes)}")
            print("NOMES=" + ",".join(nomes))

            ferramenta_cena = next(
                (nome for nome in nomes if nome == "get_objects_summary"), None
            )
            if ferramenta_cena:
                resultado = await sessao.call_tool(ferramenta_cena, {})
                print(f"CENA_OK={not resultado.isError}")
                texto = " ".join(
                    item.text for item in resultado.content if hasattr(item, "text")
                )
                print("CENA_RESUMO=" + texto[:600].replace("\n", " "))


asyncio.run(main())
