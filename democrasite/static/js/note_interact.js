/** This script contains the note interaction logic so it's only loaded for logged-in users */

$(document).ready(function () {
  const csrftoken = $("[name=csrfmiddlewaretoken]")[0].value;
  console.log(csrftoken);
  $(".note-like").click(function () {
    $.ajax($(this).attr("action"), {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken },
      context: $(this),
    }).done(function (data) {
      this.toggleClass("bi-heart");
      this.toggleClass("bi-heart-fill");
      this.parent().siblings(".note-like-count").text(data["likes"]);
    });
  });
  $(".note-repost").click(function () {
    $.ajax($(this).attr("action"), {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken },
      context: $(this),
    }).done(function (data) {
      this.toggleClass("text-secondary");
      this.toggleClass("text-success");
      this.parent().siblings(".note-repost-count").text(data["reposts"]);
    });
  });
});
