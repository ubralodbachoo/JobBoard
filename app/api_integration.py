import requests
from flask import current_app


def search_adzuna_jobs(query='', location='', results_per_page=20, page=1, country='gb'):
    app_id = current_app.config.get('ADZUNA_APP_ID')
    api_key = current_app.config.get('ADZUNA_API_KEY')

    if not app_id or not api_key:
        current_app.logger.error('Adzuna API credentials not configured')
        return None

    try:
        url = f'https://api.adzuna.com/v1/api/jobs/{country}/search/{page}'
        params = {
            'app_id': app_id,
            'app_key': api_key,
            'results_per_page': results_per_page,
            'what': query,
            'where': location,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for result in data.get('results', []):
            salary_min = result.get('salary_min')
            salary_max = result.get('salary_max')
            if salary_min and salary_max:
                salary = f"${salary_min:,.0f} - ${salary_max:,.0f}"
            elif salary_min:
                salary = f"${salary_min:,.0f}+"
            elif salary_max:
                salary = f"Up to ${salary_max:,.0f}"
            else:
                salary = 'არ არის მითითებული'

            jobs.append({
                'id': result.get('id'),
                'title': result.get('title', 'N/A'),
                'company': result.get('company', {}).get('display_name', 'N/A'),
                'location': result.get('location', {}).get('display_name', 'N/A'),
                'description': result.get('description', 'No description available'),
                'salary': salary,
                'category': result.get('category', {}).get('label', 'Other'),
                'contract_type': result.get('contract_type'),
                'created': result.get('created'),
                'redirect_url': result.get('redirect_url'),
            })

        return {
            'jobs': jobs,
            'total': data.get('count', 0),
            'page': page,
            'results_per_page': results_per_page,
        }

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f'Adzuna API request error: {e}')
        return None
    except (KeyError, ValueError) as e:
        current_app.logger.error(f'Error parsing Adzuna data: {e}')
        return None
