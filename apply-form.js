/**
 * Careers — the application form.
 *
 * Written as a plain module rather than a dc component for the same reason the
 * contact form needed its validation rewritten: the runtime strips `required`
 * from inputs when it renders, so native constraint validation never runs and
 * an empty form reports itself as valid. Here nothing is delegated to the
 * runtime, so the check is the check.
 *
 * Posts to /api/apply, which submits to the "Careers — role application" form
 * in HubSpot. That is a different form from the contact one on purpose: its own
 * GUID and its own notification, so applications can be filtered and reported
 * on separately from sales leads.
 *
 * No file upload. HubSpot's public form-submission API cannot accept one -
 * files need an authenticated upload to their Files API first - so the resume
 * is taken as a link, with the sharing note next to it because a link nobody
 * can open is worse than no link.
 */
(function () {
  "use strict";

  var INK = "#14161A", INK2 = "#3A3E45", INK3 = "#6B7078", INK4 = "#9AA0A8";
  var LINE = "#E4E4E0", LINE_SOFT = "#EFEFEC", BONE = "#F6F6F4", WHITE = "#FFFFFF";
  var BROWN = "#84512E", RED = "#A03030", FIELD = "#CFCFC9";
  var MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace";
  var SERIF = "Newsreader,Georgia,serif";

  var ROLES = [
    "Machine Learning Engineer",
    "Machine Learning Engineer Intern",
    "Founders Office",
    "Software Engineer"
  ];

  var COUNTRY_OPTIONS = "<option>Afghanistan</option><option>Albania</option><option>Algeria</option><option>Andorra</option><option>Angola</option><option>Antigua and Barbuda</option><option>Argentina</option><option>Armenia</option><option>Australia</option><option>Austria</option><option>Azerbaijan</option><option>Bahamas</option><option>Bahrain</option><option>Bangladesh</option><option>Barbados</option><option>Belarus</option><option>Belgium</option><option>Belize</option><option>Benin</option><option>Bhutan</option><option>Bolivia</option><option>Bosnia and Herzegovina</option><option>Botswana</option><option>Brazil</option><option>Brunei</option><option>Bulgaria</option><option>Burkina Faso</option><option>Burundi</option><option>Cabo Verde</option><option>Cambodia</option><option>Cameroon</option><option>Canada</option><option>Central African Republic</option><option>Chad</option><option>Chile</option><option>China</option><option>Colombia</option><option>Comoros</option><option>Congo</option><option>Congo (DRC)</option><option>Costa Rica</option><option>C\u00f4te d'Ivoire</option><option>Croatia</option><option>Cuba</option><option>Cyprus</option><option>Czechia</option><option>Denmark</option><option>Djibouti</option><option>Dominica</option><option>Dominican Republic</option><option>Ecuador</option><option>Egypt</option><option>El Salvador</option><option>Equatorial Guinea</option><option>Eritrea</option><option>Estonia</option><option>Eswatini</option><option>Ethiopia</option><option>Fiji</option><option>Finland</option><option>France</option><option>Gabon</option><option>Gambia</option><option>Georgia</option><option>Germany</option><option>Ghana</option><option>Greece</option><option>Grenada</option><option>Guatemala</option><option>Guinea</option><option>Guinea-Bissau</option><option>Guyana</option><option>Haiti</option><option>Honduras</option><option>Hong Kong</option><option>Hungary</option><option>Iceland</option><option>India</option><option>Indonesia</option><option>Iran</option><option>Iraq</option><option>Ireland</option><option>Israel</option><option>Italy</option><option>Jamaica</option><option>Japan</option><option>Jordan</option><option>Kazakhstan</option><option>Kenya</option><option>Kiribati</option><option>Kuwait</option><option>Kyrgyzstan</option><option>Laos</option><option>Latvia</option><option>Lebanon</option><option>Lesotho</option><option>Liberia</option><option>Libya</option><option>Liechtenstein</option><option>Lithuania</option><option>Luxembourg</option><option>Macao</option><option>Madagascar</option><option>Malawi</option><option>Malaysia</option><option>Maldives</option><option>Mali</option><option>Malta</option><option>Marshall Islands</option><option>Mauritania</option><option>Mauritius</option><option>Mexico</option><option>Micronesia</option><option>Moldova</option><option>Monaco</option><option>Mongolia</option><option>Montenegro</option><option>Morocco</option><option>Mozambique</option><option>Myanmar</option><option>Namibia</option><option>Nauru</option><option>Nepal</option><option>Netherlands</option><option>New Zealand</option><option>Nicaragua</option><option>Niger</option><option>Nigeria</option><option>North Korea</option><option>North Macedonia</option><option>Norway</option><option>Oman</option><option>Pakistan</option><option>Palau</option><option>Palestine</option><option>Panama</option><option>Papua New Guinea</option><option>Paraguay</option><option>Peru</option><option>Philippines</option><option>Poland</option><option>Portugal</option><option>Qatar</option><option>Romania</option><option>Russia</option><option>Rwanda</option><option>Saint Kitts and Nevis</option><option>Saint Lucia</option><option>Saint Vincent and the Grenadines</option><option>Samoa</option><option>San Marino</option><option>Sao Tome and Principe</option><option>Saudi Arabia</option><option>Senegal</option><option>Serbia</option><option>Seychelles</option><option>Sierra Leone</option><option>Singapore</option><option>Slovakia</option><option>Slovenia</option><option>Solomon Islands</option><option>Somalia</option><option>South Africa</option><option>South Korea</option><option>South Sudan</option><option>Spain</option><option>Sri Lanka</option><option>Sudan</option><option>Suriname</option><option>Sweden</option><option>Switzerland</option><option>Syria</option><option>Taiwan</option><option>Tajikistan</option><option>Tanzania</option><option>Thailand</option><option>Timor-Leste</option><option>Togo</option><option>Tonga</option><option>Trinidad and Tobago</option><option>Tunisia</option><option>T\u00fcrkiye</option><option>Turkmenistan</option><option>Tuvalu</option><option>Uganda</option><option>Ukraine</option><option>United Arab Emirates</option><option>United Kingdom</option><option>United States</option><option>Uruguay</option><option>Uzbekistan</option><option>Vanuatu</option><option>Vatican City</option><option>Venezuela</option><option>Vietnam</option><option>Yemen</option><option>Zambia</option><option>Zimbabwe</option>";

  /* name, label, type, required */
  var FIELDS = [
    ["name", "Full name *", "text", true],
    ["email", "Email *", "email", true],
    ["phone", "Phone number *", "tel", true],
    ["country", "Country *", "country", true],
    ["role", "Role you are applying for *", "role", true],
    ["school", "College or university *", "text", true],
    ["resumeLink", "Link to your resume *", "url", true],
    ["message", "Anything else you want us to know", "textarea", false]
  ];

  var PLACEHOLDER = {
    name: "Jordan Rivera",
    email: "jordan@example.com",
    phone: "+91 91008 62186",
    school: "Your college or university",
    resumeLink: "https://drive.google.com/file/d/.../view",
    message: "A system you shipped that learned something. One paragraph is plenty."
  };

  var state = { values: {}, invalid: [], status: "idle" };

  function el(tag, style, text) {
    var n = document.createElement(tag);
    if (style) n.setAttribute("style", style);
    if (text != null) n.textContent = text;
    return n;
  }

  function inputStyle(bad) {
    return "width:100%;border:1px solid " + (bad ? RED : FIELD) +
      ";border-radius:10px;padding:10px 14px;font-family:inherit;font-size:.9375rem;color:" +
      INK + ";background:" + WHITE + ";outline:none";
  }

  function control(key, type, bad) {
    var n;
    if (type === "textarea") {
      n = el("textarea", inputStyle(bad) + ";resize:vertical");
      n.rows = 4;
    } else if (type === "country" || type === "role") {
      n = el("select", inputStyle(bad) + ";cursor:pointer");
      n.innerHTML = type === "country"
        ? '<option value="">Select a country</option>' + COUNTRY_OPTIONS
        : '<option value="">Select a role</option>' +
          ROLES.map(function (r) { return "<option>" + r + "</option>"; }).join("");
    } else {
      n = el("input", inputStyle(bad));
      n.type = type;
    }
    n.id = "ap-" + key;
    if (PLACEHOLDER[key]) n.placeholder = PLACEHOLDER[key];
    n.value = state.values[key] || "";
    n.addEventListener("change", function (e) { set(key, e.target.value); });
    n.addEventListener("input", function (e) { set(key, e.target.value); });
    return n;
  }

  /* Clear a field's error as soon as it has a value, rather than making the
     applicant submit again to find out they fixed it. */
  function set(key, v) {
    state.values[key] = v;
    if (String(v || "").trim()) {
      var i = state.invalid.indexOf(key);
      if (i !== -1) {
        state.invalid.splice(i, 1);
        var n = document.getElementById("ap-" + key);
        if (n) n.style.borderColor = FIELD;
      }
    }
  }

  function validate() {
    var bad = [];
    FIELDS.forEach(function (f) {
      if (f[3] && !String(state.values[f[0]] || "").trim()) bad.push(f[0]);
    });
    var email = String(state.values.email || "").trim();
    if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(email) && bad.indexOf("email") === -1) {
      bad.push("email");
    }
    var link = String(state.values.resumeLink || "").trim();
    if (link && !/^https?:\/\/[^\s]+\.[^\s]+/i.test(link) && bad.indexOf("resumeLink") === -1) {
      bad.push("resumeLink");
    }
    return bad;
  }

  function panel(mount) {
    mount.innerHTML = "";
    var card = el("div", "border-radius:10px;border:1px solid " + LINE + ";background:" + WHITE +
      ";padding:clamp(2rem,3vw,3rem);text-align:center");
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", "46"); svg.setAttribute("height", "46");
    svg.setAttribute("viewBox", "0 0 46 46"); svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("style", "display:block;margin:0 auto 20px");
    svg.innerHTML = '<circle cx="23" cy="23" r="22" fill="none" stroke="' + BROWN +
      '" stroke-width="1.5" opacity=".3"></circle><path d="M14 23.5l6 6 12-13" fill="none" stroke="' +
      BROWN + '" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"></path>';
    card.appendChild(svg);
    var first = String(state.values.name || "").trim().split(/\s+/)[0];
    card.appendChild(el("h3", "margin:0 0 14px;font-family:" + SERIF +
      ";font-weight:400;font-size:clamp(1.5rem,1.1rem + 1vw,1.875rem);letter-spacing:-.015em;color:" + INK,
      "Application received."));
    card.appendChild(el("p", "margin:0 auto;max-width:34rem;font-size:1.0625rem;line-height:1.65;color:" + INK2,
      (first ? "Thank you, " + first + ". " : "Thank you. ") +
      "We read every one of these ourselves. If it is a fit we will come back to you directly."));
    mount.appendChild(card);
  }

  function render(mount) {
    if (state.status === "sent") return panel(mount);
    mount.innerHTML = "";

    var head = el("div", "margin-bottom:26px");
    head.appendChild(el("p", "margin:0 0 10px;font-family:" + MONO +
      ";font-weight:500;font-size:.8125rem;letter-spacing:.14em;text-transform:uppercase;color:" + INK3,
      "Apply"));
    head.appendChild(el("p", "margin:0;max-width:44rem;font-size:1.0625rem;line-height:1.6;color:" + INK2,
      "One paragraph is plenty. No cover letter."));

    var form = el("form", "border-radius:10px;border:1px solid " + LINE + ";background:" + WHITE +
      ";padding:clamp(1.75rem,2.4vw,2.25rem);box-shadow:0 1px 3px 0 rgba(20,22,26,.06)");

    var grid = el("div", "display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px");
    grid.setAttribute("data-apply-grid", "");

    FIELDS.forEach(function (f) {
      var key = f[0], wide = key === "message" || key === "resumeLink";
      var cell = el("div", "display:flex;flex-direction:column;gap:8px" +
        (wide ? ";grid-column:1/-1" : ""));
      cell.appendChild(el("label", "font-size:.875rem;font-weight:500;color:" + INK, f[1]))
        .setAttribute("for", "ap-" + key);
      cell.appendChild(control(key, f[2], state.invalid.indexOf(key) !== -1));
      if (key === "resumeLink") {
        cell.appendChild(el("p", "margin:0;font-size:.8125rem;line-height:1.5;color:" + INK3,
          "Set sharing to \u201canyone with the link can view\u201d, or we will not be able " +
          "to open it. Google Drive, Dropbox and Notion links are all fine."));
      }
      grid.appendChild(cell);
    });
    form.appendChild(grid);

    // Bots fill every field they can find, including one positioned off-screen.
    var pot = el("input", "position:absolute;left:-9999px;width:1px;height:1px;opacity:0");
    pot.type = "text"; pot.tabIndex = -1; pot.setAttribute("aria-hidden", "true");
    pot.autocomplete = "off"; pot.name = "website"; pot.id = "ap-website";
    form.appendChild(pot);

    var btn = el("button", "margin-top:26px;width:100%;padding:12px 24px;border:none;border-radius:10px;background:" +
      BROWN + ";color:#F9F9F7;font-family:inherit;font-size:.9375rem;font-weight:500;cursor:pointer",
      state.status === "sending" ? "Sending..." : "Send application");
    btn.type = "submit";
    form.appendChild(btn);

    var note = el("p", "margin:16px 0 0;text-align:center;font-size:1rem;line-height:1.6;color:" +
      (state.status === "failed" ? RED : INK3),
      state.status === "failed"
        ? "That did not send. Email team@sapientpriors.com and we will pick it up."
        : "");
    form.appendChild(note);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (state.status === "sending") return;
      var bad = validate();
      if (bad.length) {
        state.invalid = bad;
        render(mount);
        var first = document.getElementById("ap-" + bad[0]);
        if (first) { first.focus(); first.scrollIntoView({ block: "center" }); }
        return;
      }
      state.invalid = [];
      state.status = "sending";
      render(mount);
      var body = Object.assign({}, state.values);
      body.website = pot.value;
      fetch("/api/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      })
        .then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
        .then(function () { state.status = "sent"; render(mount); })
        .catch(function () { state.status = "failed"; render(mount); });
    });

    mount.appendChild(head);
    mount.appendChild(form);

    var mq = window.matchMedia("(max-width: 760px)");
    function lay() {
      grid.style.gridTemplateColumns = mq.matches ? "minmax(0,1fr)" : "repeat(2,minmax(0,1fr))";
    }
    lay();
    mq.addEventListener("change", lay);
  }

  function mount() {
    var host = document.querySelector("[data-apply-form]");
    if (!host) return false;
    if (host.getAttribute("data-mounted")) return true;
    host.setAttribute("data-mounted", "1");
    render(host);
    return true;
  }

  /*
    Mounting has to survive the runtime, not just wait for it.

    The deferred script runs before <x-dc> has been rendered, so the first
    attempt finds nothing. Waiting for the node to appear is not enough either:
    the runtime renders, then hydrates, and hydration replaces the subtree - so
    a mount that succeeds on the first appearance is wiped a moment later, with
    no error anywhere. Script 200, element present, section empty. That is what
    a bounded retry and a disconnect-on-success both produced.

    The observer is attached unconditionally, not only when the first mount
    fails. The first mount usually succeeds - on the node that is about to
    be thrown away - so making the watch conditional on failure means
    nothing is watching at the exact moment the replacement happens.

    It stays connected and re-mounts whenever the host is found without our
    content. Our own render sets data-mounted on the host, so the
    mutations we cause do not trigger another render; a host replaced by the
    runtime arrives without the attribute and is picked up on the next tick.

    Form state lives in the module, not the DOM, so a re-mount preserves
    whatever has been typed.
  */
  mount();
  var obs = new MutationObserver(function () { mount(); });
  obs.observe(document.documentElement, { childList: true, subtree: true });
})();
