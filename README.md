# CulturalContactBaetica
This is a repository for Paula Loreto Granados García PhD project "Cultural Contact in Early Roman Spain through Linked Open Data" 

# Requirements
__This software requires access to certain online spreadsheets in order to execute some data extractors. These spreadsheets are currently private.__

To run the software, be sure to have the following on your system:
- python >= 3.6
- we recommend the `pip` package manager as well

# Installation
1. Clone or download this repository
2. Enter the repository directory:

       cd CulturalContactBaetica

3. Run the setup:

       python src/setup.py install
    
# Running
You can run one or more extractors in sequence. Each extractor will generate an RDF file in Turtle format that you can load on any triple store of choice.

A single entry point is available for convenience in the form of a `baetica` module. From inside the `CulturalContactBaetica` directory, run

    python src/baetica.py [sourceNames]
    
where `sourceNames` is a space-separated list of data sources, for example:

    python src/baetica.py coinage sculpture settlements
    
Will look for `extractors/coinage.py` and execute it, then same for `extractors/sculpture.py` or `extractors/settlements.py`.

For each source there must be a Python module with that name inside the `extractors` package, so you can simply drop new ones in there.

Each extractor should generate a `.ttl` file named after the source itself inside an `out` subdirectory of the current directory, so for example: `CulturalContactBaetica/out/coinage.ttl`.

Note that existing Turtle files will be overwritten.

# License
See [LICENSE](LICENSE) file (for now).
