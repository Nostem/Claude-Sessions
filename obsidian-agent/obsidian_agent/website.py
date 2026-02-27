import json, os, subprocess

def clone_or_pull_repo(url: str, local: str):
    if os.path.exists(os.path.join(local, ".git")):
        subprocess.run(["git", "-C", local, "pull", "--rebase"], check=True)
    else:
        os.makedirs(os.path.dirname(local), exist_ok=True)
        subprocess.run(["git", "clone", url, local], check=True)

def update_bookshelf(path: str, new_book: dict):
    books = json.loads(open(path).read()) if os.path.exists(path) else []
    existing = {b.get("title","").lower() for b in books}
    if new_book.get("title","").lower() in existing:
        return
    books.append(new_book)
    with open(path, "w") as f:
        json.dump(books, f, indent=2)

def commit_and_push(repo: str, message: str):
    subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
    subprocess.run(["git", "-C", repo, "commit", "-m", message], check=True)
    subprocess.run(["git", "-C", repo, "push"], check=True)
