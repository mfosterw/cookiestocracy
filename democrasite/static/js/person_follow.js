$(document).ready(function () {
  const csrftoken = $("[name=csrfmiddlewaretoken]")[0].value;
  $(".person-follow").click(function () {
    $.ajax($(this).attr("action"), {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken },
      context: $(this),
    }).done(function (data) {
      this.toggleClass("btn-light");
      this.toggleClass("btn-dark");
      this.toggleClass("person-unfollow");
      console.log(this);
      if (this.hasClass("person-unfollow")) {
        $(this).text(""); // content comes from css
      } else {
        $(this).text("Follow");
      }
    });
  });
});
