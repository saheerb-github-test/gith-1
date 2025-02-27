import click
import requests
import logging
import sys
import time
import json
import subprocess


@click.command()
@click.pass_context
@click.option("-r", "--repository", required=True)
@click.option("-t", "--tag", required=True)
@click.option("-p", "--platform", required=False)
def get_digest(ctx, repository, tag, platform=None):
    command = f"docker run quay.io/skopeo/stable --creds={ctx.obj['username']}:{ctx.obj['passwd']} inspect docker://ghcr.io/{ctx.obj['username']}/{repository}:{tag} --raw"
    output = subprocess.run(command.split(), stdout=subprocess.PIPE).stdout.decode(
        "utf-8"
    )
    output = json.loads(output)

    logging.info(output)

@click.command()
@click.pass_context
@click.option("-r", "--repository", required=True)
@click.option("-t", "--tag", required=True)
@click.option("-p", "--platform", required=False)
def copy_image(ctx, repository, tag, platform=None):
    command =  f"docker run quay.io/skopeo/stable --src-creds={ctx.obj['username']}:{ctx.obj['passwd']} --dest-creds={ctx.obj['username']}:{ctx.obj['passwd']} copy --all docker://ghcr.io/saheerb/docker-test:latest  docker://ghcr.io/saheerb/mbed-os-env:hacked-123" 
    output = subprocess.run(command.split(), stdout=subprocess.PIPE).stdout.decode(
        "utf-8"
    )

    print(output)
    

# delete images older than provided argument (number_of_days)
@click.command()
@click.pass_context
@click.option("-r", "--repository", required=True)
@click.option(
    "-n",
    "--number_of_days",
    default="1",
    help="number of days since image was created",
    required=False,
)
def delete_old_images(ctx, repository, number_of_days):
    s = requests.Session()
    github_api_accept = "application/vnd.github.v3+json"
    s.headers.update(
        {"Authorization": f'token {ctx.obj["passwd"]}', "Accept": github_api_accept}
    )
    r = s.get(f"https://api.github.com/user/packages/container/{repository}/versions")
    versions = r.json()

    version_id = None
    pattern = "%d.%m.%Y %H:%M:%S"
    pattern = "%Y-%m-%dT%H:%M:%SZ"
    current_time = time.time()

    for version in versions:
        epoch = int(time.mktime(time.strptime(version["updated_at"], pattern)))

        if (current_time - epoch) / (24 * 60 * 60) > int(number_of_days):
            version_id = version["id"]
            logging.debug(f"deleteing image with version id {version_id}")

            url = f"https://api.github.com/user/packages/container/{repository}/versions/{version_id}"
            resp = s.delete(url)
            resp.raise_for_status()


@click.group()
@click.pass_context
@click.option("-u", "--username", required=False)
@click.option("-p", "--passwd", required=False)
@click.option("-v", "--verbose", is_flag=True, default=False)
def main(ctx, username, passwd, verbose):
    ctx.obj = {"username": username, "passwd": passwd}

    if verbose:
        logging.basicConfig(
            stream=sys.stdout,
            format="%(levelname)s %(asctime)s %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.basicConfig(
            format="%(levelname)s %(asctime)s %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )
        logging.getLogger().setLevel(logging.INFO)


if __name__ == "__main__":
    main.add_command(get_digest)
    main.add_command(delete_old_images)
    main.add_command(copy_image)
    main()
