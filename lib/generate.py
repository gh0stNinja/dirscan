from operator import itemgetter


def generate_html(results, sort_by=None, filter_status=None):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dir Scanner Results</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f2f2f2;
                margin: 0;
                padding: 20px;
            }

            h1 {
                color: #333333;
                margin-top: 0;
            }

            table {
                border-collapse: collapse;
                width: 100%;
            }

            th, td {
                padding: 8px;
                text-align: left;
                border-bottom: 1px solid #dddddd;
            }

            tr:nth-child(even) {
                background-color: #f9f9f9;
            }

            .sortable {
                cursor: pointer;
            }
        </style>
        <script>
            function sortTable(column) {
                const table = document.getElementById("results-table");
                const rows = Array.from(table.getElementsByTagName("tr"));
                const headerRow = rows.shift();
                const columnIndex = Array.from(headerRow.getElementsByTagName("th")).findIndex(th => th.innerText === column);
                const ascending = headerRow.getElementsByTagName("th")[columnIndex].classList.contains("ascending");
                const sortedRows = rows.sort((a, b) => {
                    const aVal = a.getElementsByTagName("td")[columnIndex].innerText;
                    const bVal = b.getElementsByTagName("td")[columnIndex].innerText;
                    return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                });
                table.innerHTML = "";
                table.appendChild(headerRow);
                sortedRows.forEach(row => table.appendChild(row));
                headerRow.getElementsByTagName("th")[columnIndex].classList.toggle("ascending");
            }

            function filterTable() {
                const filter = document.getElementById("filter-input").value.toLowerCase();
                const table = document.getElementById("results-table");
                const rows = Array.from(table.getElementsByTagName("tr"));
                rows.forEach(row => {
                    const columns = Array.from(row.getElementsByTagName("td"));
                    const shouldShow = columns.some(column => column.innerText.toLowerCase().includes(filter));
                    row.style.display = shouldShow ? "" : "none";
                });
            }
        </script>
    </head>
    <body>
        <h1>Dir Scanner Results</h1>
        <div>
            <label for="filter-input">Filter:</label>
            <input type="text" id="filter-input" oninput="filterTable()">
        </div>
        <table id="results-table">
            <tr>
                <th class="sortable" onclick="sortTable('URL')">URL</th>
                <th class="sortable" onclick="sortTable('Status Code')">Status Code</th>
                <th class="sortable" onclick="sortTable('Content Length')">Content Length</th>
            </tr>
    """

    results = sorted(results, key=itemgetter(sort_by)) if sort_by else results


    for result in results:
        url = result["url"]
        status_code = result["status"]
        content_length = result["contentLength"]

        if filter_status and status_code != filter_status:
            continue

        html += f"""
            <tr>
                <td><a href="{url}">{url}</a></td>
                <td>{status_code}</td>
                <td>{content_length}</td>
            </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return html

