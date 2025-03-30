import base64

import requests
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

LANGUAGE_EXTENSIONS = {
    'python': 'py',
    'java': 'java',
    'cpp': 'cpp h hpp',
    'go': 'go',
    'rust': 'rs'
}

GITHUB_TOKEN = ''

headers = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': f'Bearer {GITHUB_TOKEN}'
}


def search_code(query, language, max_results=50):
    url = 'https://api.github.com/search/code'
    extensions = LANGUAGE_EXTENSIONS.get(language, '')
    params = {
        'q': f'"{query}" in:file extension:{extensions}',
        'per_page': max_results
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print("Ошибка:", response.status_code, response.text)
        return []

    data = response.json()
    potential_results = data.get('items', [])

    valid_results = []

    for item in potential_results:
        repo_name = item['repository']['full_name']
        file_path = item['path']

        valid_results.append({
            'repo_name': repo_name,
            'file_name': item['name'],
            'file_path': file_path,
            'url': item['html_url']
        })

    return valid_results


def get_file_content(repo_name, file_path):
    url = f'https://api.github.com/repos/{repo_name}/contents/{file_path}'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Ошибка получения файла:", response.status_code, response.text)
        return ""

    content = response.json().get('content', '')
    decoded_content = base64.b64decode(content).decode('utf-8', errors='ignore')
    return decoded_content


@app.route('/', methods=['GET'])
def index():
    query = request.args.get('query', '')
    language = request.args.get('language', 'cpp')
    languages = ['python', 'java', 'cpp', 'go', 'rust']

    if query:
        if session.get('last_query') == query and session.get('last_language') == language:
            results = session.get('search_results', [])
        else:
            results = search_code(query, language)
            session['search_results'] = results
            session['last_query'] = query
            session['last_language'] = language
    else:
        results = []

    return render_template('index.html', results=results, query=query, selected_language=language, languages=languages)


@app.route('/view_code')
def view_code():
    repo = request.args.get('repo')
    path = request.args.get('path')
    query = request.args.get('query')
    language = request.args.get('language', 'cpp')

    code = get_file_content(repo, path)

    if query not in code:
        return redirect(url_for('index', query=query, language=language))

    github_url = f'https://github.com/{repo}/blob/master/{path}'

    return render_template('view_code.html', code=code, query=query, repo=repo, path=path, language=language,
                           github_url=github_url)


if __name__ == '__main__':
    app.run(debug=True)
