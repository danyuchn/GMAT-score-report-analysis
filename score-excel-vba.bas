Attribute VB_Name = "Module1"
'------------------------------------------------------------
' Sub: MarkOverTime_Incorrect_And_Unusual_Q
' Description: Marks overtime and too-fast cells; sets rows with "Incorrect" performance to red font;
'              and checks for UNUSUAL condition based on Fundamental Skill.
' Note: The functionality of outputting incorrect question numbers to K25 has been removed.
'------------------------------------------------------------
Sub MarkOverTime_Incorrect_And_Unusual_Q()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim i As Long, j As Long
    Dim responseTime As Double
    Dim threshold As Double, lowerLimit As Double
    Dim fundamentalSkill As String
    Dim currentDifficulty As Double
    Dim candidateDifficulty As Double
    Dim isUnusual As Boolean
    Dim isUnusualSlow As Boolean
    
    ' Set recommended response time and lower limit (in minutes)
    threshold = 2.5
    lowerLimit = 1
    
    ' Set slow response time threshold (in minutes) for unusual slow check
    Dim slowThreshold As Double
    slowThreshold = 3
    
    ' Assume data is in the active sheet
    Set ws = ActiveSheet
    lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row
    
    ' First loop: Mark overtime and too-fast cells, and mark rows with "Incorrect" in red font.
    For i = 2 To lastRow
        responseTime = ws.Cells(i, "B").Value ' Response Time (Minutes) is in column B
        
        ' If response time is greater than threshold (2.5 minutes), color cell in light yellow.
        If responseTime > threshold Then
            ws.Cells(i, "B").Interior.Color = RGB(255, 255, 153)
        End If
        
        ' If response time is less than lower limit (1 minute), color cell in green.
        If responseTime < lowerLimit Then
            ws.Cells(i, "B").Interior.Color = vbGreen
        End If
        
        ' If Performance (column C) is "Incorrect", set the entire row's font color to red.
        If ws.Cells(i, "C").Value = "Incorrect" Then
            ws.Rows(i).Font.Color = vbRed
        End If
    Next i
    
    ' Second loop: For each Incorrect record, check if its V_b is lower than any Correct record in the same Fundamental Skill group.
    For i = 2 To lastRow
        If ws.Cells(i, "C").Value = "Incorrect" Then
            fundamentalSkill = ws.Cells(i, "F").Value  ' Fundamental Skill is in column F
            currentDifficulty = ws.Cells(i, "G").Value   ' V_b value is in column G
            isUnusual = False
            
            ' Check all records in the same Fundamental Skill group
            For j = 2 To lastRow
                If ws.Cells(j, "F").Value = fundamentalSkill Then
                    If ws.Cells(j, "C").Value = "Correct" Then
                        ' If any correct record has a V_b greater than the current difficulty, mark as unusual.
                        If ws.Cells(j, "G").Value > currentDifficulty Then
                            isUnusual = True
                            Exit For
                        End If
                    End If
                End If
            Next j
            
            ' If condition met, mark column H with "UNUSUAL".
            If isUnusual Then
                ws.Cells(i, "H").Value = "UNUSUAL"
            End If
        End If
    Next i
    
    ' Third loop: For each record with response time > slowThreshold (3 minutes), check unusual slow condition.
    For i = 2 To lastRow
        If ws.Cells(i, "B").Value > slowThreshold Then
            fundamentalSkill = ws.Cells(i, "F").Value  ' Fundamental Skill from column F
            currentDifficulty = ws.Cells(i, "G").Value   ' Current record's V_b from column G
            isUnusualSlow = False
            
            ' Loop through all records in the same Fundamental Skill group.
            For j = 2 To lastRow
                If ws.Cells(j, "F").Value = fundamentalSkill Then
                    ' Check if record j is answered correctly and has lower response time than record i.
                    If ws.Cells(j, "C").Value = "Correct" Then
                        If ws.Cells(j, "B").Value < ws.Cells(i, "B").Value Then
                            candidateDifficulty = ws.Cells(j, "G").Value
                            ' If candidate's difficulty is greater than current record's difficulty, mark as unusual slow.
                            If candidateDifficulty > currentDifficulty Then
                                isUnusualSlow = True
                                Exit For
                            End If
                        End If
                    End If
                End If
            Next j
            
            ' If condition met, mark column H with "UNUSUAL SLOW".
            If isUnusualSlow Then
                ws.Cells(i, "H").Value = "UNUSUAL SLOW"
            End If
        End If
    Next i
    
    MsgBox "Analysis complete. (Q version)", vbInformation, "Analysis Complete"
End Sub

'------------------------------------------------------------
' Sub: MarkOverTime_Incorrect_And_Unusual_Slow_V
' Description: Marks too fast and overtime cells based on question type; sets rows with "Incorrect"
'              performance to red font; and checks for UNUSUAL and UNUSUAL SLOW conditions.
' Note: The functionality of outputting incorrect question numbers to K25 has been removed.
'------------------------------------------------------------
Sub MarkOverTime_Incorrect_And_Unusual_Slow_V()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim i As Long, j As Long
    Dim responseTime As Double
    Dim crThreshold As Double, defaultThreshold As Double, lowerLimit As Double
    Dim slowThreshold As Double
    Dim currentQuestionType As String
    Dim fundamentalSkill As String
    Dim currentDifficulty As Double
    Dim candidateDifficulty As Double
    Dim isUnusual As Boolean
    Dim isUnusualSlow As Boolean

    ' Set thresholds
    crThreshold = 2
    defaultThreshold = 2.5
    lowerLimit = 0.5
    slowThreshold = 3

    Set ws = ActiveSheet
    lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row

    ' First loop: Mark too fast and overtime cells
    For i = 2 To lastRow
        responseTime = ws.Cells(i, "B").Value
        currentQuestionType = ws.Cells(i, "E").Value

        Dim currentThreshold As Double
        If currentQuestionType = "Critical Reasoning" Then
            currentThreshold = crThreshold
        ElseIf currentQuestionType = "Reading Comprehension" Then
            currentThreshold = 0 ' No overtime marking for RC
        Else
            currentThreshold = defaultThreshold
        End If

        ' Mark too fast: below lower limit marked as light green
        If responseTime < lowerLimit Then
            ws.Cells(i, "B").Interior.Color = RGB(144, 238, 144)
        ElseIf currentThreshold > 0 Then
            If responseTime > currentThreshold Then
                ws.Cells(i, "B").Interior.Color = RGB(255, 255, 153)
            End If
        End If

        ' If Performance is "Incorrect", mark the row in red
        If ws.Cells(i, "C").Value = "Incorrect" Then
            ws.Rows(i).Font.Color = vbRed
        End If
    Next i

    ' Second loop: Determine UNUSUAL condition for "Incorrect" rows
    For i = 2 To lastRow
        If ws.Cells(i, "C").Value = "Incorrect" Then
            fundamentalSkill = ws.Cells(i, "F").Value
            currentDifficulty = ws.Cells(i, "G").Value
            isUnusual = False
            For j = 2 To lastRow
                If ws.Cells(j, "F").Value = fundamentalSkill Then
                    If ws.Cells(j, "C").Value = "Correct" Then
                        If ws.Cells(j, "G").Value > currentDifficulty Then
                            isUnusual = True
                            Exit For
                        End If
                    End If
                End If
            Next j
            If isUnusual Then
                ws.Cells(i, "H").Value = "UNUSUAL"
            End If
        End If
    Next i

    ' Third loop: Determine UNUSUAL SLOW condition for rows with response time > slowThreshold
    For i = 2 To lastRow
        If ws.Cells(i, "B").Value > slowThreshold Then
            fundamentalSkill = ws.Cells(i, "F").Value
            currentDifficulty = ws.Cells(i, "G").Value
            isUnusualSlow = False
            For j = 2 To lastRow
                If ws.Cells(j, "F").Value = fundamentalSkill Then
                    If ws.Cells(j, "C").Value = "Correct" Then
                        If ws.Cells(j, "B").Value < ws.Cells(i, "B").Value Then
                            candidateDifficulty = ws.Cells(j, "G").Value
                            If candidateDifficulty > currentDifficulty Then
                                isUnusualSlow = True
                                Exit For
                            End If
                        End If
                    End If
                End If
            Next j
            If isUnusualSlow Then
                ws.Cells(i, "H").Value = "UNUSUAL SLOW"
            End If
        End If
    Next i

    MsgBox "Analysis complete for V section.", vbInformation, "Analysis Complete"
End Sub

'------------------------------------------------------------
' Sub: MarkOverTime_Incorrect_And_Unusual_Slow_DI
' Description: Marks too fast and overtime cells based on question type; sets rows with "Incorrect"
'              performance to red font; and checks for UNUSUAL and UNUSUAL SLOW conditions.
' Note: The functionality of outputting incorrect question numbers to K25 has been removed.
'------------------------------------------------------------
Sub MarkOverTime_Incorrect_And_Unusual_Slow_DI()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim i As Long, j As Long
    Dim responseTime As Double
    Dim recommendedTime As Double
    Dim lowerLimit As Double
    Dim slowThreshold As Double
    Dim qType As String
    Dim fundamentalSkill As String
    Dim currentDifficulty As Double
    Dim candidateDifficulty As Double
    Dim isUnusual As Boolean
    Dim isUnusualSlow As Boolean

    lowerLimit = 0.5
    slowThreshold = 3

    Set ws = ActiveSheet
    lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row

    ' First loop: Mark too fast and overtime cells
    For i = 2 To lastRow
        responseTime = ws.Cells(i, "B").Value
        qType = ws.Cells(i, "E").Value

        Select Case qType
            Case "Data Sufficiency"
                recommendedTime = 2
            Case "Two-part analysis", "Graph and Table"
                recommendedTime = 3
            Case "Multi-source Reasoning"
                recommendedTime = -1
            Case Else
                recommendedTime = 2.5
        End Select

        If responseTime < lowerLimit Then
            ws.Cells(i, "B").Interior.Color = RGB(144, 238, 144)
        ElseIf recommendedTime <> -1 Then
            If responseTime > recommendedTime Then
                ws.Cells(i, "B").Interior.Color = RGB(255, 255, 153)
            End If
        End If

        ' If Performance is "Incorrect", mark the row in red
        If ws.Cells(i, "C").Value = "Incorrect" Then
            ws.Rows(i).Font.Color = vbRed
        End If
    Next i

    ' Second loop: Determine UNUSUAL condition for "Incorrect" rows
    For i = 2 To lastRow
        If ws.Cells(i, "C").Value = "Incorrect" Then
            fundamentalSkill = ws.Cells(i, "F").Value
            currentDifficulty = ws.Cells(i, "G").Value
            isUnusual = False
            For j = 2 To lastRow
                If ws.Cells(j, "F").Value = fundamentalSkill Then
                    If ws.Cells(j, "C").Value = "Correct" Then
                        If ws.Cells(j, "G").Value > currentDifficulty Then
                            isUnusual = True
                            Exit For
                        End If
                    End If
                End If
            Next j
            If isUnusual Then
                ws.Cells(i, "H").Value = "UNUSUAL"
            End If
        End If
    Next i

    ' Third loop: Determine UNUSUAL SLOW condition for rows with response time > slowThreshold
    For i = 2 To lastRow
        If ws.Cells(i, "B").Value > slowThreshold Then
            fundamentalSkill = ws.Cells(i, "F").Value
            currentDifficulty = ws.Cells(i, "G").Value
            isUnusualSlow = False
            For j = 2 To lastRow
                If ws.Cells(j, "F").Value = fundamentalSkill Then
                    If ws.Cells(j, "C").Value = "Correct" Then
                        If ws.Cells(j, "B").Value < ws.Cells(i, "B").Value Then
                            candidateDifficulty = ws.Cells(j, "G").Value
                            If candidateDifficulty > currentDifficulty Then
                                isUnusualSlow = True
                                Exit For
                            End If
                        End If
                    End If
                End If
            Next j
            If isUnusualSlow Then
                ws.Cells(i, "H").Value = "UNUSUAL SLOW"
            End If
        End If
    Next i

    MsgBox "Analysis complete for DI section.", vbInformation, "Analysis Complete"
End Sub

'------------------------------------------------------------
' Sub: OutputIncorrectList
' Description: Searches for records with "Incorrect" performance in column C,
'              accumulates the question numbers from column A (comma-separated),
'              and outputs the result to cell K25.
'------------------------------------------------------------
Sub OutputIncorrectList()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim i As Long
    Dim incorrectList As String  ' Accumulate incorrect question numbers

    ' Set the active worksheet
    Set ws = ActiveSheet
    lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row

    ' Initialize the incorrect list string
    incorrectList = ""

    ' Loop through each row from 2 to lastRow
    For i = 2 To lastRow
        ' If Performance in column C is "Incorrect", accumulate the question number from column A
        If ws.Cells(i, "C").Value = "Incorrect" Then
            If incorrectList = "" Then
                incorrectList = ws.Cells(i, "A").Value
            Else
                incorrectList = incorrectList & "," & ws.Cells(i, "A").Value
            End If
        End If
    Next i

    ' Output the accumulated incorrect question numbers to cell K25
    ws.Range("K25").Value = incorrectList

    MsgBox "Incorrect question numbers output to K25.", vbInformation, "Output Complete"
End Sub

'----------------------------------------------------------------------
' Generate Plain Text Report with Color Information
Sub GeneratePlainTextReport_WithColorInfo()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim i As Long
    Dim reportText As String
    Dim marker As String
    Dim questionNumber As Variant
    Dim responseTime As Variant
    Dim performance As String
    Dim questionType As String
    Dim fundamentalSkill As String
    Dim difficulty As Variant
    Dim cellColor As Long
    Dim colorMarker As String
    Dim includeRow As Boolean
    
    ' Set worksheet and find the last row
    Set ws = ActiveSheet
    lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row
    
    reportText = "GMAT Analysis Report:" & vbCrLf & vbCrLf
    reportText = reportText & "?Color Marking Explanation?:" & vbCrLf
    reportText = reportText & "  - [Yellow]: Overtime - indicates the response time exceeds the recommended time." & vbCrLf
    reportText = reportText & "  - [Green]: Too Fast - indicates the response time is below the lower limit." & vbCrLf & vbCrLf
    reportText = reportText & "?Marker Explanation?:" & vbCrLf
    reportText = reportText & "  - UNUSUAL: Abnormal condition where a simple (low difficulty) question is answered incorrectly while a harder question in the same subgroup is answered correctly." & vbCrLf
    reportText = reportText & "  - UNUSUAL SLOW: Indicates the response time is excessively long compared to other correct answers in the same subgroup with higher difficulty." & vbCrLf
    reportText = reportText & String(40, "-") & vbCrLf & vbCrLf
    
    ' Loop through each row (assuming row 1 contains headers)
    For i = 2 To lastRow
        marker = ws.Cells(i, "H").Value
        cellColor = ws.Cells(i, "B").Interior.Color
        ' Set colorMarker based on cell background color
        colorMarker = ""
        If cellColor = RGB(255, 255, 153) Then
            colorMarker = "[Yellow]"
        ElseIf cellColor = RGB(144, 238, 144) Then
            colorMarker = "[Green]"
        End If
        
        ' Decide whether to include the row:
        ' Include if marker is not empty or if the cell background is Yellow or Green.
        includeRow = (marker <> "") Or (cellColor = RGB(255, 255, 153)) Or (cellColor = RGB(144, 238, 144))
        
        If includeRow Then
            questionNumber = ws.Cells(i, "A").Value
            responseTime = ws.Cells(i, "B").Value
            performance = ws.Cells(i, "C").Value
            questionType = ws.Cells(i, "E").Value
            fundamentalSkill = ws.Cells(i, "F").Value
            difficulty = ws.Cells(i, "G").Value
            
            reportText = reportText & "Question: " & questionNumber & vbCrLf
            reportText = reportText & "  Response Time: " & responseTime & " minutes " & IIf(colorMarker <> "", colorMarker, "") & vbCrLf
            reportText = reportText & "  Performance: " & performance & vbCrLf
            reportText = reportText & "  Question Type: " & questionType & vbCrLf
            reportText = reportText & "  Fundamental Skill: " & fundamentalSkill & vbCrLf
            reportText = reportText & "  Difficulty (V_b): " & difficulty & vbCrLf
            reportText = reportText & "  Marker: " & marker & vbCrLf
            reportText = reportText & String(40, "-") & vbCrLf
        End If
    Next i
    
    ' Output the report to a new worksheet
    Dim reportWs As Worksheet
    Set reportWs = Worksheets.Add
    reportWs.Range("A1").Value = reportText
    
    MsgBox "Report generated on a new worksheet. Please copy and paste the text for further AI analysis.", vbInformation, "Report Generated"
End Sub


