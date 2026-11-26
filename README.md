## exa

**Author:** yevanchen
**Version:** 0.1.0
**Type:** tool


### Contact
![Exa Logo](./_assets/image%20copy.png)


### Description

Exa is an AI-powered search tool that enables semantic search and content retrieval using Exa's advanced API.

![Exa Logo](./_assets/image.png)

## Tools

### 1. Exa Search (`exa_search`)

Search the web and optionally extract highlights or full text from the results.

#### Parameters:

- **query** (string, required): The search query to find relevant information on the web.
- **search_type** (select, optional, default: `auto`). Choose `auto`, `lite`, `deep-lite`, or `deep`. Lite uses cached content.
- **num_results** (number, optional, default: 10): Maximum number of search results (1-100)
- **include_domains** (string, optional): Comma-separated list of domains to include in results
- **exclude_domains** (string, optional): Comma-separated list of domains to exclude from results
- **start_published_date** (string, optional): Only include results published after this date (YYYY-MM-DD)
- **end_published_date** (string, optional): Only include results published before this date (YYYY-MM-DD)
- **max_age_hours** (number, optional). Maximum cache age in hours. Use `0` for live content or `-1` for cache only. Leave this unset in Lite mode.
- **include_highlights** (boolean, optional, default: true): Return query-relevant excerpts from each result
- **highlights_max_characters** (number, optional). Maximum combined highlight length per result.
- **include_text** (boolean, optional, default: false): Return full page text (opt-in)
- **category** (select, optional): Focus on specific data categories
  - Options are `company`, `people`, `publication`, `news`, `personal site`, and `financial report`.
  - Company and People searches require leaving publication dates unset. People searches also require leaving domain exclusions unset.

### 2. Exa URL Contents (`exa_contents`)

Get highlights, optional full text, links, and subpages for up to 100 URLs. The JSON response includes a status for each URL.

Returns results from Exa's cache, with automatic live crawling as fallback for uncached pages.

#### Parameters:

- **urls** (string, required): Comma-separated list of URLs to extract content from
- **max_age_hours** (number, optional): Freshness control. 0 = always crawl, -1 = cache only, 24 = cache if less than 24h old
- **include_highlights** (boolean, optional, default: true): Return query-relevant excerpts from each page
- **highlights_max_characters** (number, optional). Maximum combined highlight length per page.
- **full_page_text** (boolean, optional, default: false): Return full page text (opt-in)
- **number_of_subpages** (number, optional, default: 1): Number of subpages to include in content extraction
- **return_links** (number, optional, default: 1): Number of links to return from each webpage

### 3. Exa Answer (`exa_answer`)

Provide a question in `query` to get an answer with citations. Enable `text` to include the cited pages' text. Choose `exa`, `exa-pro`, `exa-research`, or `exa-fast` as the model.

## Acknowledgements



Special thanks to [@ExaAILabs](https://x.com/ExaAILabs) for providing the powerful API that powers this plugin.



