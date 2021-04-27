import aiohttp
import json
from baguette import Baguette, Request, View
from baguette.httpexceptions import (
    BadRequest,
    Forbidden,
    NotImplemented,
    NotFound,
)

app = Baguette(error_response_type="json")


@app.route("/webhooks/<webhook_path:path>", name="webhook")
class WebhookHandler(View):
    with open("webhooks.json") as f:
        webhooks = json.load(f)
        # name: {token: ..., **kwargs}
        # name: {name: {token: ..., **kwargs}}

    async def post(self, request: Request, webhook_path: str):
        webhooks = self.webhooks
        for name in webhook_path.split("/"):
            if name not in webhooks:
                raise NotFound(description="Unknown webhook")

            webhooks = webhooks[name]

        webhook = webhooks

        if webhook.get("token", "") not in request.querystring.get(
            "token", [""]
        ):
            raise Forbidden(description="Bad token")

        for name in webhook_path.split("/"):
            handler = getattr(self, name, None)
            if handler is not None:
                break

        if handler is None:
            raise NotImplemented(  # noqa: F901
                description="Handler for this webhook isn't implemented"
            )

        return await handler(request, webhook)

    async def readthedocs(self, request: Request, webhook):
        if "discord_webhook_url" not in webhook:
            raise NotFound(description="Unknown webhook")

        try:
            data = await request.json()
        except ValueError:
            raise BadRequest(description=str(ValueError))

        title = "[{}] Read The Docs build ".format(data["slug"])
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
