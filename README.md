# Umbrella

A small and simple service for coverage badges working with public repos the service host has access to via GitHub Token Authentification.

It looks for an artifact created by a workflow called `coverage.yml`. The artifact must contain a xml file called `cobertura.xml` which may be created using `cargo tarpaulin`.

The Endpoint returns an image in typical badge format. ![](https://coverage.jenskrumsieck.de/coverage/fairagro/m4.4_sciwin_client)

# How to use
+ Fork the repo into your own account and 
+ Link the repository to a new vercel project
+ Create a GitHub personal access token with the scope set to `repo`. 
+ Add this token to vercel as environment variable `API_TOKEN`. 
+ The badge will now be available at `https://whateverpage.org/coverage/{:user}/{:repo}/?branch={:optional}`. 

For example `https://coverage.jenskrumsieck.de/coverage/fairagro/m4.4_sciwin_client?branch=feature/tool_create`: ![](https://coverage.jenskrumsieck.de/coverage/fairagro/m4.4_sciwin_client?branch=feature/tool_create)