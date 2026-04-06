# Usage Guide

This guide describes the main workflows in the Funding Research App.

## 1. Call Summarization

The process usually begins with a new research call:

1. Enter the URL for the research call (e.g., BMBF, BMWK).
2. Click **Analyze Call**.
3. The app automatically extracts:
   - **Metadata**: Deadline, budget, funding rate.
   - **Description**: A detailed summary of research goals.
   - **Eligible Applicants**: Who is allowed to participate (e.g., SMEs).

## 2. FIT Search

If you don't have a specific call yet, search in the FIT database:

1. Enter search terms like "AI" or "Sustainability".
2. Click **Search FIT**.
3. The app fetches current calls and uses LLMs to assess relevance for your request.

## 3. Company Indexing

To enable matching, you must add companies to the database:

1. **Manual Link**: Enter a URL.
2. **Folder Scan**: Specify a path to a local folder with `.url` files.
3. The app crawls the websites, creates summaries, and stores them as vectors in the database.

## 4. Matching & Hybrid Search

Find the right partners for a research project:

1. **Auto-Matching**: Automatically selects a previously analyzed call.
2. **Hybrid Search**: Uses both SQL filters (e.g., only SMEs from NRW) and semantic search (vector comparison).
3. **Project Proposals**: Let the AI generate concrete project ideas based on the found partners.

## 5. Database View

Manage your partners:

1. View all indexed companies in a table.
2. Use the **Map** to locate companies geographically (currently focusing on NRW).
3. Edit metadata directly in the app.
