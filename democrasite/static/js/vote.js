/** This script contains the voting logic and is thus only loaded for logged-in users */

function update_progress(_, pbar) {
  let votes = $(pbar).siblings(".vote");
  let yes_votes = parseInt(votes.children(".num-yes-votes").text());
  let no_votes = parseInt(votes.children(".num-no-votes").text());
  $(pbar)
    .children()
    .first()
    .css("width", ((100 * yes_votes) / (yes_votes + no_votes) || 0) + "%");

  $(pbar)
    .children()
    .last()
    .css("width", ((100 * no_votes) / (yes_votes + no_votes) || 0) + "%");
}

$(document).ready(function () {
  const csrftoken = $("[name=csrfmiddlewaretoken]")[0].value;
  console.log(csrftoken);
  $(".vote").click(function () {
    // Don't let users vote on expired bills
    if ($(this).parent().hasClass("inactive")) {
      return;
    }

    $.ajax($(this).attr("action"), {
      method: "POST",
      headers: { "X-CSRFToken": csrftoken },
      data: { vote: $(this).attr("value") },
      context: $(this),
    }).done(function (data) {
      this.toggleClass("fw-bold");
      this.siblings(".vote").removeClass("fw-bold");
      num = this.attr("id").split("-").slice(-1)[0];
      $("#num-vote-yes-" + num).text(data["yes-votes"]);
      $("#num-vote-no-" + num).text(data["no-votes"]);
      update_progress(0, this.siblings(".progress"));
    });
  });
});
