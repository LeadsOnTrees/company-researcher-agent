# Company Researching Agent

<h3>
  <img src="imgs/logo.png" alt="logo" width="50" style="vertical-align: middle;" />
  by <a href="https://leadsontrees.com">leadsontrees.com</a>
</h3>

<video controls src="imgs/demo.mp4" title="Title"></video>

# What is this about?

This is a tool that helps you research a company by scraping the web and generating a report.

Save time instead of browsing manually through the company's website. Use this tool to get a quick overview of the company's website, careers, funding, and more.


# How this works?

- The tool uses a browser to scrape the company's website.
This agent will deep crawl a website and extract all the information it can find.
It will skip some unnecessary pages like the documentation, support pages, etc.

- It then uses a series of prompts to extract the information you need. There's a lot of valuable information from career pages, FAQ sections, blog posts. This gives you a lot of insights what tech stack the company uses and what the company might be interested to buy.

- The tool generates a report in PDF format. Which you can save and share with your team.

# How to use

Setup env keys:

```bash
export OPENAI_API_KEY=...
export DEEPSEEK_API_KEY=...

# Default is gpt-4o-mini
export LLM_MODEL=o3-mini

# Optional - if you want to use LeadsOnTrees API for funding data
export LOT_API_KEY=...
```

Launching:

```bash
uv sync
uv run research https://example.com
```

If you want to research a very large website it can be good to reduce the max response count:

```bash
uv run research https://example.com --max-results 30
```

However, the more pages you scrape the more data LLM will have to give you better insights.


# What is LeadsOnTrees?

LeadsOnTrees is a platform which aggregates all VC funded startups and their founders.

We scrape news, blogs, and other sources to find new startups and investments.

This data is then used to generate insights about the startup ecosystem.

See more on [leadsontrees.com](https://leadsontrees.com)