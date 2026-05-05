# Nutzungsleitfaden

Dieser Leitfaden beschreibt die Hauptarbeitsabläufe in der Förderrecherche App.

## 1. Ausschreibungs-Zusammenfassung

Der Prozess beginnt in der Regel mit einer neuen Ausschreibung:

1. Geben Sie die URL zur Ausschreibung ein (z.B. BMBF, BMWK).  
2. Klicken Sie auf **Ausschreibung analysieren**.  
3. Die App extrahiert automatisch:  
   - **Metadaten**: Deadline, Budget, Förderquote.  
   - **Beschreibung**: Eine detaillierte Zusammenfassung der Forschungsziele.  
   - **Antragsberechtigte**: Wer darf teilnehmen (z.B. KMUs).  

## 2. FIT Suche

Wenn Sie noch keinen konkreten Call haben, suchen Sie in der FIT-Datenbank:

1. Geben Sie Suchbegriffe wie "KI" oder "Nachhaltigkeit" ein.  
2. Klicken Sie auf **FIT durchsuchen**.  
3. Die App ruft aktuelle Aufrufe ab und nutzt LLMs, um die Relevanz für Ihre Anfrage zu bewerten.  

## 3. Unternehmens-Indexierung

Damit das Matching funktioniert, müssen Sie Unternehmen in die Datenbank aufnehmen:

1. **Manueller Link**: Geben Sie eine URL ein.  
2. **Ordner-Scan**: Geben Sie einen Pfad zu einem lokalen Ordner mit `.url`-Dateien an.  
3. Die App crawlt die Webseiten, erstellt Zusammenfassungen und speichert diese als Vektoren in der Datenbank.  

## 4. Matching & Hybrid-Suche

Finden Sie die passenden Partner für ein Forschungsprojekt:

1. **Auto-Matching**: Wählt automatisch einen zuvor analysierten Call aus.  
2. **Hybrid-Suche**: Nutzt sowohl SQL-Filter (z.B. nur KMUs aus NRW) als auch semantische Suche (Vektorvergleich).  
3. **Projektvorschläge**: Lassen Sie die KI konkrete Projektideen generieren, basierend auf den gefundenen Partnern.  

## 5. Datenbank-Ansicht

Verwalten Sie Ihre Partner:

1. Sehen Sie alle indexierten Unternehmen in einer Tabelle.  
2. Nutzen Sie die **Karte**, um Unternehmen geografisch zu verorten (derzeit Fokus auf NRW).  
3. Bearbeiten Sie Metadaten direkt in der App.  
