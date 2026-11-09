"""Manually upload reviewed source to an existing PRIVATE Docker Space."""
import argparse
import re
from release_bundle import release_files

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("space_id", help="OWNER/SPACE, already created as private Docker Space")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", args.space_id):
        parser.error("Expected OWNER/SPACE")
    files = release_files()
    # Uses HF_TOKEN or the user's existing Hugging Face login. Never prints it.
    from huggingface_hub import HfApi, CommitOperationAdd
    api = HfApi()
    info = api.repo_info(repo_id=args.space_id, repo_type="space")
    if not info.private:
        raise SystemExit("Refusing public target. Use a private Space for this unauthenticated keyed prototype.")
    if info.sdk != "docker":
        raise SystemExit("Target must be a Docker Space.")
    operations = [CommitOperationAdd(path_in_repo=name, path_or_fileobj=body)
                  for name, body in files if not name.startswith(".github/")]
    api.create_commit(repo_id=args.space_id, repo_type="space", operations=operations,
                      commit_message="Deploy reviewed PromoProof source")
    print(f"Uploaded {len(operations)} source files to https://huggingface.co/spaces/{args.space_id}")
    print("No runtime secrets were set or copied. Configure them in Space Settings.")

if __name__ == "__main__":
    main()
