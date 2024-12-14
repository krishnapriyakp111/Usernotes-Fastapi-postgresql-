function deleteNote(noteId) {
  fetch("/views/delete-note", {
    method: "DELETE",
    body: JSON.stringify({ noteId: noteId }),
  }).then((_res) => {
    window.location.href = "/views/main";
  });
}
