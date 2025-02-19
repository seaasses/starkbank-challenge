from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/")
async def root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stark Bank Challenge</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }
            h1 {
                color: #2d3748;
                border-bottom: 2px solid #4a5568;
                padding-bottom: 10px;
            }
            h2 {
                color: #4a5568;
                margin-top: 30px;
            }
            ul {
                padding-left: 20px;
            }
            li {
                margin: 10px 0;
            }
            code {
                background-color: #f7fafc;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            }
            .highlight {
                background-color: #ebf8ff;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <h1>Stark Bank Challenge</h1>
        
        <div class="highlight">
            <p>Workspace: <code>marcuslacerda.sandbox.starkbank.com</code><br>
            Domain: <code><a href="https://stark-challenge.com">stark-challenge.com</a></code><br>
            GitHub: <a href="https://github.com/seaasses/starkbank-challenge">seaasses/starkbank-challenge</a></p>
        </div>

        <h2>Project Overview</h2>
        <p>A FastAPI application that integrates with Stark Bank's API to handle invoices and webhooks.</p>

        <h2>Key Features</h2>
        <ul>
            <li>Automatic webhook creation in the workspace</li>
            <li>Scheduled job running every 3 hours to generate 8-12 invoices using the bank client</li>
            <li>Webhook endpoint (<code>/api/v1/webhooks/starkbank</code>) for receiving Stark Bank events</li>
            <li>Daily job to process unconsumed events</li>
        </ul>

        <h2>Security Features</h2>
        <ul>
            <li>Event signature verification</li>
            <li>Protection against replay attacks using Redis-based distributed cache</li>
            <li>Maximum event age validation</li>
        </ul>

        <h2>Technical Stack</h2>
        <ul>
            <li>FastAPI for the web framework</li>
            <li>Redis for distributed caching and locking</li>
            <li>Docker for containerization</li>
            <li>AWS (ECR, ECS, Elasticache) for deployment</li>
            <li>Terraform for infrastructure as code</li>
        </ul>

        <h2>API Endpoints</h2>
        <ul>
            <li><code><a href="/api/v1/webhooks/starkbank">/api/v1/webhooks/starkbank</a></code> - Webhook endpoint for Stark Bank events</li>
            <li><code><a href="/health">/health</a></code> - Health check endpoint</li>
        </ul>

        <h2>Local Development</h2>
        <p>To run the project locally:</p>
        <ol>
            <li>Create a <code>.env</code> file with required environment variables</li>
            <li>Run <code>docker compose up</code></li>
            <li>The webhook will be automatically created and services will start</li>
            <li>Hot reload is enabled for development</li>
        </ol>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")
