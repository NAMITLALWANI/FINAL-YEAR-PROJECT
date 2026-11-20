# White book: what only the team can fill in

Everything that cannot be known from the project is a yellow `[bracketed]` placeholder in `HAMMER_WhiteBook.docx`.
Use Word's Find (Ctrl/Cmd+F, search `[`) to jump through them. After typing, select all (Ctrl/Cmd+A) and set
Home > Text Highlight Color > No Color so the yellow disappears from typed text.

| Where | Placeholder | Notes |
|---|---|---|
| Title page | Student 1-4 names, Roll Nos. | Delete unused rows if the group has fewer than four |
| Title page | Guide name and designation | |
| Title page | Group ID | Also needed for the Classroom file name: `Group ID_project title` |
| Certificate, Declaration, Approval pages | Date | Leave the signature lines blank; they are signed by hand |
| Acknowledgements | Guide name, Head of Department name, Principal name | |

After filling: right-click the Contents, List of Figures and List of Tables > Update Field > Update entire table
(Word also offers to update fields when the file opens; choose Yes). Then File > Export > PDF for the Classroom upload.

Pages ii-iv (certificate, declaration, approval of examiners) are the "initial certificate pages": print two copies for the examiners.

Rebuild (optional): `python3 whitebook/build/build_all.py <scratch dir>` regenerates the PDF and the DOCX from the content files in `whitebook/build/`.
Edit the chapter text in `content_*.py`; the name, roll number and guide placeholders are in `content_a.py`.
