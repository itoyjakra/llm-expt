import arxiv
import datetime
import pandas as pd

def search_arxiv_llm_papers(num_papers=10):
    # Define the search query
    query = "Large Language Models"
    
    # Calculate the date 30 days ago
    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    
    # Search for papers
    search = arxiv.Search(
        query=query,
        max_results=num_papers,
        start=0,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    # Filter papers from the last 30 days
    papers = []
    for result in search.get():
        if result.submitted_date >= thirty_days_ago:
            papers.append({
                'Title': result.title,
                'Authors': ', '.join(result.authors),
                'Abstract': result.abstract,
                'Link': result.id,
                'Submitted Date': result.submitted_date
            })
    
    # Optionally, save the extracted information to a CSV file
    df = pd.DataFrame(papers)
    df.to_csv('arxiv_llm_papers.csv', index=False)
    
    return papers

if __name__ == "__main__":
    papers = search_arxiv_llm_papers(num_papers=10)
    if papers:
        print("Search completed successfully.")
    else:
        print("Search failed.")
