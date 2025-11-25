import requests
from flask import current_app


def search_adzuna_jobs(query='', location='', results_per_page=20, page=1, country='gb'):
    """
    Search for jobs using Adzuna API.
    Returns a list of job postings from Adzuna.
    
    Supported countries: gb, us, de, au, ca, fr, it, nl, pl, ru, etc.
    """
    app_id = current_app.config.get('ADZUNA_APP_ID')
    api_key = current_app.config.get('ADZUNA_API_KEY')
    
    if not app_id or not api_key:
        current_app.logger.error('Adzuna API credentials not configured')
        return None
    
    try:
        # Adzuna API endpoint for specified country
        url = f'https://api.adzuna.com/v1/api/jobs/{country}/search/{page}'
        
        params = {
            'app_id': app_id,
            'app_key': api_key,
            'results_per_page': results_per_page,
            'what': query,  # Job title or keywords
            'where': location,  # Location
            'content-type': 'application/json'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        jobs = []
        for result in data.get('results', []):
            job_info = {
                'id': result.get('id'),
                'title': result.get('title', 'N/A'),
                'company': result.get('company', {}).get('display_name', 'N/A'),
                'location': result.get('location', {}).get('display_name', 'Georgia'),
                'description': result.get('description', 'No description available'),
                'salary_min': result.get('salary_min'),
                'salary_max': result.get('salary_max'),
                'category': result.get('category', {}).get('label', 'Other'),
                'contract_type': result.get('contract_type'),
                'created': result.get('created'),
                'redirect_url': result.get('redirect_url'),
                'latitude': result.get('latitude', 41.7151),
                'longitude': result.get('longitude', 44.8271)
            }
            
            # Format salary
            if job_info['salary_min'] and job_info['salary_max']:
                job_info['salary'] = f"${job_info['salary_min']:,.0f} - ${job_info['salary_max']:,.0f}"
            elif job_info['salary_min']:
                job_info['salary'] = f"${job_info['salary_min']:,.0f}+"
            elif job_info['salary_max']:
                job_info['salary'] = f"Up to ${job_info['salary_max']:,.0f}"
            else:
                job_info['salary'] = 'არ არის მითითებული'
            
            jobs.append(job_info)
        
        current_app.logger.info(f'Adzuna API: Found {len(jobs)} jobs for query: {query}')
        
        return {
            'jobs': jobs,
            'total': data.get('count', 0),
            'page': page,
            'results_per_page': results_per_page
        }
    
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f'Adzuna API request error: {str(e)}')
        return None
    except (KeyError, ValueError) as e:
        current_app.logger.error(f'Error parsing Adzuna data: {str(e)}')
        return None

