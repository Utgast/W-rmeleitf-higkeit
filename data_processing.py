import pandas as pd
import os
import time

# Überprüfen, ob das Modul dbfread installiert ist, und gegebenenfalls installieren
try:
    from dbfread import DBF
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "dbfread"])
    from dbfread import DBF

def read_dbf_file(file_path):
    encodings = ['latin1', 'utf-8', 'cp1252']
    for encoding in encodings:
        try:
            table = DBF(file_path, encoding=encoding)
            df = pd.DataFrame(iter(table))
            print(f"Datei erfolgreich mit Encoding '{encoding}' gelesen.")
            return df
        except UnicodeDecodeError as e:
            print(f"Fehler beim Lesen der Datei mit Encoding '{encoding}': {e}")
    raise UnicodeDecodeError("Kein gültiges Encoding gefunden, um die Datei zu lesen.")

def test_data_processing():
    try:
        # 1. Öffnen der Tabelle aus der angegebenen DBF-Datei
        input_file_path = r"C:\Users\reinhard2074\OneDrive - ARCADIS\Desktop\NeueCSV\ALL_TOEB_FL_20576_AGE_l_r15_250128.dbf"
        df = read_dbf_file(input_file_path)
        print("DataFrame nach dem Öffnen der Datei:")
        print(df)

        # Überprüfen der Spaltennamen
        print("Spaltennamen der Datei:")
        print(df.columns)

        # Überprüfen, ob die erforderlichen Spalten vorhanden sind
        required_columns = ['Art', 'Typ', 'Material', 'ID_KO']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Erforderliche Spalte '{col}' fehlt in der Datei.")

        # 2. Ersetzen von "Sonstiges" oder "Sonstige" in Spalte Typ
        df['Typ'] = df.apply(lambda row: row['Art'] if row['Typ'] in ['Sonstiges', 'Sonstige'] else row['Typ'], axis=1)
        print("DataFrame nach Ersetzen von 'Sonstiges' oder 'Sonstige':")
        print(df)

        # 3. Ergänzen von Spalte Kommentar
        df['Kommentar'] = df['ID_KO'] + ', ' + df['Material']
        print("DataFrame nach Ergänzen von Spalte 'Kommentar':")
        print(df)

        # ...existing code...

        # Ausgabe des DataFrames zur Überprüfung
        print("Endgültiger DataFrame:")
        print(df)

        # Festlegen des Speicherverzeichnisses
        save_directory = r"C:\Users\reinhard2074\OneDrive - ARCADIS\Desktop\NeueCSV"
        print(f"Speicherverzeichnis: {save_directory}")

        # Überprüfen, ob das Verzeichnis existiert, und gegebenenfalls erstellen
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
            print(f"Verzeichnis erstellt: {save_directory}")
        else:
            print(f"Verzeichnis existiert bereits: {save_directory}")

        # Speichern des DataFrames als CSV-Datei im angegebenen Verzeichnis
        save_path_csv = os.path.join(save_directory, "bearbeitete_tabelle.csv")
        if os.path.exists(save_path_csv):
            print(f"Datei {save_path_csv} existiert bereits und wird überschrieben.")
            os.remove(save_path_csv)  # Entferne die vorhandene Datei, um sie zu überschreiben
        df.to_csv(save_path_csv, index=False, encoding='utf-8-sig')
        print(f"DataFrame als CSV gespeichert unter: {save_path_csv}")

        # Speichern des DataFrames als sortierbare HTML-Datei im angegebenen Verzeichnis
        save_path_html = os.path.join(save_directory, "bearbeitete_tabelle.html")
        if os.path.exists(save_path_html):
            print(f"Datei {save_path_html} existiert bereits und wird überschrieben.")
            os.remove(save_path_html)  # Entferne die vorhandene Datei, um sie zu überschreiben

        # HTML-Datei mit korrekter Darstellung von Umlauten erstellen
        html_content = df.to_html(index=False, classes='sortable')
        html_content = f"""
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <title>Bearbeitete Tabelle</title>
            <style>
                table.sortable {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                table.sortable th, table.sortable td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                }}
                table.sortable th {{
                    cursor: pointer;
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            {html_content}
            <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
                    const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
                        v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
                    )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));
                    document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {{
                        const table = th.closest('table');
                        Array.from(table.querySelectorAll('tr:nth-child(n+2)'))
                            .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
                            .forEach(tr => table.appendChild(tr) );
                    }})));
                }});
            </script>
        </body>
        </html>
        """
        with open(save_path_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"DataFrame als HTML gespeichert unter: {save_path_html}")

        # Ausgabe des Links zur gespeicherten Datei
        print(f"Die bearbeitete Tabelle wurde erfolgreich unter {save_path_csv} und {save_path_html} gespeichert.")
        print(f"Öffnen Sie die CSV-Datei hier: file:///{save_path_csv}")
        print(f"Öffnen Sie die HTML-Datei hier: file:///{save_path_html}")

    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        print(f"Fehlerdetails: {e.__class__.__name__} - {e}")

if __name__ == "__main__":
    print("Starte das Datenverarbeitungs-Skript...")
    test_data_processing()
    print("Datenverarbeitungs-Skript abgeschlossen.")
