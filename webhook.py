import aiohttp
import json
from baguette import Baguette, Request, View
from baguette.httpexceptions import BadRequest, Forbidden, NotImplemented

app = Baguette(error_response_type="json")

with open("webhooks.json") as f:
    webhooks = json.load(f)  # id: {func_name: ..., token: ..., **kwargs}


@app.route("/webhooks/<webhook_id>", name="webhook")
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

        title = "[{}] Read The Docs build ".format(data["slug"]
        url = "https://readthedocs.org/projects/{}/builds/{}".format(
            data["slug"], data["build"]["id"]
        )

        if data["build"]["state"] == "triggered":
            title += "started"
            color = 3447003

        else:
            title += "{} on commit ``{}``".format(
                "success" if data["build"]["success"] else "failure",
                data["build"]["commit"][:7],
            )
            color = 38912 if data["build"]["success"] else 16525609

        discord_embed = {
            "title": title,
            "url": url,
            "color": color,
        }

        discord_webhook = {"embeds": [discord_embed]}

        async with aiohttp.ClientSession() as session:
            await session.post(
                webhook["discord_webhook_url"], json=discord_webhook
            )

        return {"success": True}
