import aiohttp
import json
from baguette import Baguette, Request, View
from baguette.httpexceptions import BadRequest, Forbidden, NotImplemented

app = Baguette(error_response_type="json")

with open("webhooks.json") as f:
    webhooks = json.load(f)  # id: {func_name: ..., token: ..., **kwargs}


@app.route("/<webhook_id>", name="webhook")
class WebhookHandler(View):
    async def post(self, request: Request, webhook_id: str):
        if webhook_id not in webhooks:
            raise BadRequest(description="Unknown webhook")

        webhook = webhooks[webhook_id]

        if webhook["token"] not in request.querystring.get("token", [""]):
            raise Forbidden(description="Bad token")

        handler = getattr(self, webhook["func_name"], None)
        if handler is None:
            raise NotImplemented(  # noqa: F901
                description="Handler for this webhook isn't implemented"
            )

        return await handler(request, webhook)

    async def readthedocs_to_discord(self, request: Request, webhook):
        try:
            data = await request.json()
        except ValueError:
            raise BadRequest(str(ValueError))

        print(data, flush=True)

        discord_embed = {
            "title": "[baguette] Read The Docs build {} on commit ``{}``".format(
                "success" if data["build"]["success"] else "failure",
                data["build"]["commit"][:7],
            ),
            "url": "https://readthedocs.org/projects/baguette/builds/{}/".format(
                data["build"]["id"]
            ),
            "color": 38912 if data["build"]["success"] else 16525609,
        }

        discord_webhook = {"embeds": [discord_embed]}

        async with aiohttp.ClientSession() as session:
            await session.post(
                webhook["discord_webhook_url"], json=discord_webhook
            )

        return {"success": True}
