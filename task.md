#Build Jira comment updater using the python libs supports below features 
	- scapes the XLS containts Incidents list and store it in duckdb using vector text embaddings
	- fetch the details from the stored vector and create a query to match the jira description and load the similar data from duckdb	
	- do the historical analysis using llm to determine similar fixes or Jira description
	- use the above analysis to update the similar jira comments which includes the past Jira references, code snippets, Pull request etc.
	- use the LLM model for above analysis