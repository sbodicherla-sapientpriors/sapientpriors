"""
Make the home-page contact form real.

As exported it is decorative. The inputs carry required="" in the source, but
the runtime strips the attribute when it renders — form.checkValidity() returns
true with every field empty — so the asterisks promised a check that did not
exist. The handler was `e.preventDefault(); setState({sent:true})`: no
validation, no request, and a "Message received" label. Every lead was
discarded while the UI claimed success.

Because the runtime removes the attribute, validation has to live in the submit
handler. This rewrites it, adds phone and country, and points the form at
/api/contact.
"""
import os

WRAP = '<div style="margin-bottom:24px;display:flex;flex-direction:column;gap:8px">'
LBL = 'style="font-size:.875rem;font-weight:500"'
IN_TAIL = ("border-radius:10px;padding:10px 14px;font-family:inherit;"
           "font-size:.9375rem;color:#14161A;background:#FFFFFF;outline:none")


def field(fid, label, binding, setter, border, placeholder, typ=""):
    t = 'type="%s" ' % typ if typ else ""
    return (
        '%s\n                <label for="%s" %s>%s</label>\n'
        '                <input id="%s" %srequired="" placeholder="%s" '
        'value="{{ %s }}" onChange="{{ %s }}" '
        'style="border:1px solid {{ %s }};%s">\n'
        '              </div>\n              '
        % (WRAP, fid, LBL, label, fid, t, placeholder, binding, setter, border, IN_TAIL)
    )

# "Which model are you on?" started life on the Try It form only, which meant
# the answer arrived for demo leads and never for the ones who came through the
# home page - the more qualified half. It is the single most useful thing a
# lead can tell us before the call, so it is asked in both places now, and it
# stays optional: someone who has not decided yet should not be blocked by it.
def model_field(fid, binding, setter):
    return (
        '%s\n                <label for="%s" %s>Which model are you on? (optional)</label>\n'
        '                <input id="%s" placeholder="GPT-4o, Claude, Gemini, your own" '
        'value="{{ %s }}" onChange="{{ %s }}" '
        'style="border:1px solid #CFCFC9;%s">\n'
        '              </div>\n              '
        % (WRAP, fid, LBL, fid, binding, setter, IN_TAIL)
    )


# ISO 3166-1 short names. A free-text country field looks fine in testing and
# then arrives as "USA", "U.S.", "united states" and "Murica" in the inbox,
# which makes the field useless for routing or reporting.
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain",
    "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
    "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada",
    "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros",
    "Congo", "Congo (DRC)", "Costa Rica", "Côte d'Ivoire", "Croatia", "Cuba",
    "Cyprus", "Czechia", "Denmark", "Djibouti", "Dominica", "Dominican Republic",
    "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia",
    "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia",
    "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau",
    "Guyana", "Haiti", "Honduras", "Hong Kong", "Hungary", "Iceland", "India",
    "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan",
    "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos",
    "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania",
    "Luxembourg", "Macao", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali",
    "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia",
    "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar",
    "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger",
    "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau",
    "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines",
    "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino",
    "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles",
    "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia",
    "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan",
    "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania",
    "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia",
    "Türkiye", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates",
    "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu",
    "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe",
]


def country_select():
    """
    A native <select>, deliberately not a styled custom widget.

    The browser's own control already handles type-ahead, keyboard navigation,
    screen readers and the mobile wheel picker. Re-implementing that to gain a
    matching chevron is a bad trade on a form whose entire job is to not lose
    the lead.
    """
    opts = ['<option value="">Select a country</option>']
    opts += ["<option>%s</option>" % c for c in COUNTRIES]
    return (
        '%s\n                <label for="sp-country" %s>Country *</label>\n'
        '                <select id="sp-country" required="" value="{{ formCountry }}" '
        'onChange="{{ setCountry }}" '
        'style="border:1px solid {{ bdCountry }};%s;cursor:pointer">%s</select>\n'
        '              </div>\n              '
        % (WRAP, LBL, IN_TAIL, "".join(opts))
    )


OLD_SETFIELD = """  setField(key) {
    return e => {
      const v = e.target.value;
      this.setState(s => {
        const form = Object.assign({}, s.form);
        form[key] = v;
        return { form: form };
      });
    };
  }"""

# Clear a field's error the moment it is filled, rather than making the visitor
# submit again to find out they fixed it. Without this the red border survives
# until the next submit, which reads as "still wrong" while they are typing.
NEW_SETFIELD = """  setField(key) {
    return e => {
      const v = e.target.value;
      this.setState(s => {
        const form = Object.assign({}, s.form);
        form[key] = v;
        const invalid = String(v || '').trim()
          ? s.invalid.filter(k => k !== key)
          : s.invalid;
        return {
          form: form,
          invalid: invalid,
          status: s.status === 'error' && invalid.length === 0 ? 'idle' : s.status
        };
      });
    };
  }"""

OLD_SUBMIT = """  submit = e => {
    e.preventDefault();
    this.setState({ sent: true });
  };"""

NEW_SUBMIT = """  borderFor(key) {
    return this.state.invalid.indexOf(key) === -1 ? '#CFCFC9' : '#A03030';
  }

  /*
    The runtime strips `required` from the inputs when it renders, so native
    constraint validation never runs — form.checkValidity() is true with every
    field empty. What follows is therefore the only check on the client, and
    the server repeats it for exactly the same reason.
  */
  submit = e => {
    e.preventDefault();
    const f = this.state.form;
    const need = ['name', 'email', 'phone', 'company', 'country', 'useCase'];
    const invalid = need.filter(k => !String(f[k] || '').trim());
    const email = String(f.email || '').trim();
    if (email && !/^[^@\\s]+@[^@\\s]+\\.[^@\\s]{2,}$/.test(email) && invalid.indexOf('email') === -1) {
      invalid.push('email');
    }
    if (invalid.length) {
      this.setState({ invalid: invalid, status: 'error' });
      const id = 'sp-' + (invalid[0] === 'useCase' ? 'usecase' : invalid[0]);
      const first = document.getElementById(id);
      if (first) { first.focus(); first.scrollIntoView({ block: 'center' }); }
      return;
    }
    this.setState({ invalid: [], status: 'sending' });
    fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(f)
    })
      .then(r => { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
      .then(() => this.setState({ sent: true, status: 'sent' }))
      .catch(() => this.setState({ status: 'failed' }));
  };"""

OLD_NOTE = """      formNote: this.state.sent
        ? "We'll come back to you within 48 hours to book the working session."
        : 'No cost, no obligation. We reply within 48 hours.',"""

NEW_NOTE = """      formNote: this.state.sent
        ? 'Thank you — we have it, and we will come back to you to book the session.'
        : this.state.status === 'failed'
          ? 'That did not send. Email team@sapientpriors.com and we will pick it up.'
          : '',"""


def apply(out):
    touched = 0
    for name in ("SapientPriors.dc.html", "index.html"):
        p = os.path.join(out, name)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        if "sp-phone" in s:
            continue
        before = s

        anchor = s.find('<label for="sp-company"')
        w = s.rfind(WRAP, 0, anchor)
        if w != -1:
            block = (field("sp-phone", "Phone number *", "formPhone", "setPhone",
                           "bdPhone", "+81 3 1234 5678", "tel")
                     + country_select())
            s = s[:w] + block + s[w:]

        for fid, b in (("sp-name", "bdName"), ("sp-email", "bdEmail"),
                       ("sp-company", "bdCompany"), ("sp-usecase", "bdUseCase")):
            i = s.find('id="%s"' % fid)
            if i == -1:
                continue
            tag = s[s.rfind("<input", 0, i):s.find(">", i) + 1]
            s = s.replace(tag, tag.replace("border:1px solid #CFCFC9",
                                           "border:1px solid {{ %s }}" % b))

        # model goes between "what keeps forgetting" and the free-text box
        msg_wrap = ('<div style="margin-bottom:28px;display:flex;'
                    'flex-direction:column;gap:8px">')
        if msg_wrap in s:
            s = s.replace(msg_wrap,
                          model_field("sp-model", "formModel", "setModel") + msg_wrap, 1)

        # the textarea used to ask for the model in its placeholder; it has its
        # own field now, and a form that asks the same thing twice reads as
        # sloppy to exactly the people we want taking us seriously
        s = s.replace("placeholder=\"Volume, timeline, the model you're on.\"",
                      'placeholder="Volume, timeline, anything else we should know."')

        s = s.replace(
            '<p style="margin:16px 0 0;text-align:center;font-size:1rem;line-height:1.6;'
            'color:#6B7078">{{ formNote }}</p>',
            '<p style="margin:16px 0 0;text-align:center;font-size:1rem;line-height:1.6;'
            'color:{{ noteColour }}">{{ formNote }}</p>')

        s = s.replace(
            "form: { name: '', email: '', company: '', useCase: '', message: '' }, sent: false,",
            "form: { name: '', email: '', phone: '', company: '', country: '', useCase: '', "
            "model: '', message: '' }, sent: false, invalid: [], status: 'idle',")

        s = s.replace(
            "      formName: this.state.form.name,",
            "      formName: this.state.form.name,\n"
            "      formPhone: this.state.form.phone,\n"
            "      formModel: this.state.form.model,\n"
            "      formCountry: this.state.form.country,")
        s = s.replace(
            "      setName: this.setField('name'),",
            "      setName: this.setField('name'),\n"
            "      setPhone: this.setField('phone'),\n"
            "      setModel: this.setField('model'),\n"
            "      setCountry: this.setField('country'),")
        s = s.replace(
            "      submitForm: this.submit,",
            "      bdName: this.borderFor('name'),\n"
            "      bdEmail: this.borderFor('email'),\n"
            "      bdPhone: this.borderFor('phone'),\n"
            "      bdCompany: this.borderFor('company'),\n"
            "      bdCountry: this.borderFor('country'),\n"
            "      bdUseCase: this.borderFor('useCase'),\n"
            "      noteColour: this.state.status === 'failed' ? '#A03030' : '#6B7078',\n"
            "      submitForm: this.submit,")
        s = s.replace(
            "      submitLabel: this.state.sent ? 'Message received' : 'Book the working session',",
            "      submitLabel: this.state.status === 'sending' ? 'Sending...'\n"
            "        : this.state.sent ? 'Request received' : 'Book the working session',")
        s = s.replace(OLD_SETFIELD, NEW_SETFIELD)
        s = s.replace(OLD_NOTE, NEW_NOTE)
        s = s.replace(OLD_SUBMIT, NEW_SUBMIT)

        if s != before:
            open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
            touched += 1
    if touched:
        print("contact form")
        print("  phone + country added, validation and /api/contact wired (%d files)" % touched)


SUCCESS_BODY = (
    '<div style="STYLE;text-align:center">\n'
    '              <svg width="46" height="46" viewBox="0 0 46 46" aria-hidden="true" '
    'style="display:block;margin:0 auto 20px">\n'
    '                <circle cx="23" cy="23" r="22" fill="none" stroke="#84512E" '
    'stroke-width="1.5" opacity=".3"></circle>\n'
    '                <path d="M14 23.5l6 6 12-13" fill="none" stroke="#84512E" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"></path>\n'
    '              </svg>\n'
    '              <h3 style="margin:0 0 14px;font-family:Newsreader,Georgia,serif;'
    'font-weight:400;font-size:clamp(1.5rem,1.1rem + 1vw,1.875rem);letter-spacing:-.015em;'
    'color:#14161A">Request received.</h3>\n'
    '              <p style="margin:0 auto 26px;max-width:34rem;font-size:1.0625rem;'
    'line-height:1.65;color:#3A3E45">{{ sentBody }}</p>\n'
    '            </div>'
)


def shorten(out):
    """
    Cut the contact form to four fields.

    Every field is a place to abandon. Name, work email and company are what a
    first reply needs; the rest - country, which assistant forgets, which model,
    free text - are questions for the call, not the form. Phone stays but stops
    being required.

    The removed fields are removed, not hidden: a hidden input still posts, and
    a CRM column quietly filling with empty strings is worse than a column that
    is honestly absent.

    Note this depends on phone, country and message being optional on the
    HubSpot form. They are required there by default, and the submission API
    returns 400 REQUIRED_FIELD for each one missing - so the form has to be
    updated on that side or every lead fails at the last step.
    """
    import os
    import re as _re
    for name in ("SapientPriors.dc.html", "index.html", "TryIt.dc.html"):
        p = os.path.join(out, name)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        before = s

        # Balanced scan from the wrapper. Counting "one </div> past the label"
        # works for <div><label><input></div> and overshoots by one for a
        # <select>, whose wrapper closes at the first </div> - so removing the
        # country field also swallowed the company field that followed it.
        def close_div(t, start):
            depth, k = 0, start
            while k < len(t):
                if t.startswith("<div", k):
                    depth += 1
                elif t.startswith("</div>", k):
                    depth -= 1
                    if depth == 0:
                        return k + len("</div>")
                k += 1
            return -1

        for fid in ("sp-country", "sp-usecase", "sp-model", "sp-message"):
            i = s.find('id="%s"' % fid)
            if i == -1:
                continue
            w = s.rfind('<div style="margin-bottom:', 0, i)
            end = close_div(s, w)
            if end == -1:
                print("  %s: unbalanced wrapper - CHECK" % fid)
                continue
            s = s[:w] + s[end:]

        s = s.replace("Book the working session", "Book a Demo")
        s = s.replace("Phone number *", "Phone number (optional)")

        # the client check follows the fields that still exist
        # Regex, not a literal: the two forms list the same fields in a
        # different order (company before country on one, after on the other),
        # so a literal matched one file and silently skipped the other.
        s = _re.sub(r"const need = \[[^\]]*\];",
                    "const need = ['name', 'email', 'company'];", s)

        if s != before:
            open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
            print("  %-24s form cut to four fields" % name)


def apply_success_state(out):
    """
    Swap the form for a confirmation panel once it has been submitted.

    Leaving the filled fields on screen under a one-line note is genuinely
    ambiguous: the visitor cannot tell whether it sent, whether it is still
    editable, or whether pressing the button again would send a duplicate. The
    commonest response is to press it again.

    The form element carries the card styling, so the panel reuses that exact
    style string rather than a copy — if the card is restyled in the design,
    both states move together instead of drifting apart.
    """
    import os
    for name in ("SapientPriors.dc.html", "index.html"):
        p = os.path.join(out, name)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        if "{{ sentBody }}" in s:
            continue

        i = s.find('<form onSubmit="{{ submitForm }}"')
        if i == -1:
            continue
        st = s.find('style="', i) + len('style="')
        card_style = s[st:s.find('"', st)]
        j = s.find("</form>", i) + len("</form>")
        form_html = s[i:j]

        block = ('<sc-if value="{{ notSent }}">' + form_html + '</sc-if>'
                 '<sc-if value="{{ sent }}">'
                 + SUCCESS_BODY.replace("STYLE", card_style)
                 + '</sc-if>')
        s = s[:i] + block + s[j:]

        s = s.replace(
            "      submitForm: this.submit,",
            "      sent: this.state.sent,\n"
            "      notSent: !this.state.sent,\n"
            "      sentBody: (() => {\n"
            "        const first = String(this.state.form.name || '').trim().split(/\\s+/)[0];\n"
            "        return (first ? 'Thank you, ' + first + '. ' : 'Thank you. ')\n"
            "          + 'We will come back to you shortly with a slot for your working session.';\n"
            "      })(),\n"
            "      submitForm: this.submit,")

        # The sent branch of the note now lives in the panel, so the note only
        # has to carry a failed send.
        s = s.replace(
            "      formNote: this.state.sent\n"
            "        ? 'Thank you — we have it, and we will come back to you to book the session.'\n"
            "        : this.state.status === 'failed'",
            "      formNote: this.state.status === 'failed'")
        s = s.replace(
            "          ? 'That did not send. Email team@sapientpriors.com and we will pick it up.'\n"
            "          : '',",
            "        ? 'That did not send. Email team@sapientpriors.com and we will pick it up.'\n"
            "        : '',")

        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
        print("  " + name + "  form swaps to a confirmation panel on submit")


def unify_tryit_form(out):
    """
    Make the Try It form the same form as the home page - by copying it.

    The previous version of this reproduced the home form field by field, which
    is how the two drifted: Try It kept "Roughly how many users?" and a
    segmented control that exists nowhere else, the labels disagreed
    ("What keeps forgetting?" against "Which assistant keeps forgetting?"), and
    only Try It asked which model you were on. Two forms feeding one CRM with
    different questions means the columns are populated for some contacts and
    empty for others, and nobody can tell why.

    So this lifts the finished home block verbatim - the form, the confirmation
    panel and the sc-if that swaps between them - and installs it here. The ids
    stay sp-* because the two forms are on different pages and never collide,
    and keeping them identical is the point: any future change to the home form
    arrives here for free.

    All that remains page-specific is the component behind it, which is
    rewritten below to publish exactly the binding names the copied markup
    expects.
    """
    import os
    p = os.path.join(out, "TryIt.dc.html")
    home = os.path.join(out, "SapientPriors.dc.html")
    if not (os.path.exists(p) and os.path.exists(home)):
        return
    h = open(home, encoding="utf-8", errors="surrogateescape").read()
    s = open(p, encoding="utf-8", errors="surrogateescape").read()
    if "sp-usecase" in s:
        return

    # ---- the markup: lift the whole swap, not just the form ----------------
    a = h.find('<sc-if value="{{ notSent }}"><form onSubmit="{{ submitForm }}"')
    if a == -1:
        print("  TryIt.dc.html  home form block not found - CHECK")
        return
    b = h.find("</sc-if>", h.find('<sc-if value="{{ sent }}"', a))
    block = h[a:b + len("</sc-if>")]

    i = s.find('<form onSubmit="{{ submit }}"')
    j = s.find("</form>", i)
    if i == -1 or j == -1:
        print("  TryIt.dc.html  local form not found - CHECK")
        return
    s = s[:i] + block + s[j + len("</form>"):]

    # ---- the component: publish the names the copied markup asks for -------
    # Matched by regex rather than by literal: what patch_tryit leaves here has
    # changed twice already, and a literal that silently stops matching gives a
    # component whose markup asks for bindings the state never had - which
    # renders as a blank section, not an error.
    import re as _re
    s, n = _re.subn(
        r"state = \{[^}]*\};",
        "state = { name: '', email: '', phone: '', country: '', company: '', useCase: '', "
        "model: '', message: '', sent: false, invalid: [], status: 'idle' };",
        s, count=1)
    if not n:
        print("  TryIt.dc.html  state initialiser not found - CHECK")

    # borderFor, and a field() that clears a field's error as soon as it has a
    # value rather than making the visitor submit again to find out they fixed
    # it. The copied markup binds every input's border to borderFor, so without
    # this the component throws on first render.
    old_field = """  field(key) {
    return e => {
      const v = e.target.value;
      this.setState(s => {
        const next = {};
        next[key] = v;
        return next;
      });
    };
  }"""
    new_field = """  borderFor(key) {
    return this.state.invalid.indexOf(key) === -1 ? '#CFCFC9' : '#A03030';
  }

  field(key) {
    return e => {
      const v = e.target.value;
      this.setState(s => {
        const next = {};
        next[key] = v;
        next.invalid = String(v || '').trim()
          ? s.invalid.filter(k => k !== key)
          : s.invalid;
        next.status = s.status === 'error' && next.invalid.length === 0 ? 'idle' : s.status;
        return next;
      });
    };
  }"""
    if old_field not in s:
        print("  TryIt.dc.html  field() not found - CHECK")
    s = s.replace(old_field, new_field, 1)

    old_start = s.index("      sizes: SIZES.map(label => ({")
    old_end = s.index("      setModel: this.field('model'),") + len("      setModel: this.field('model'),")
    s = s[:old_start] + """      formName: s.name,
      formEmail: s.email,
      formPhone: s.phone,
      formCountry: s.country,
      formCompany: s.company,
      formUseCase: s.useCase,
      formModel: s.model,
      formMessage: s.message,
      setName: this.field('name'),
      setEmail: this.field('email'),
      setPhone: this.field('phone'),
      setCountry: this.field('country'),
      setCompany: this.field('company'),
      setUseCase: this.field('useCase'),
      setModel: this.field('model'),
      setMessage: this.field('message'),
      bdName: this.borderFor('name'),
      bdEmail: this.borderFor('email'),
      bdPhone: this.borderFor('phone'),
      bdCountry: this.borderFor('country'),
      bdCompany: this.borderFor('company'),
      bdUseCase: this.borderFor('useCase'),
      sent: s.sent,
      notSent: !s.sent,
      noteColour: s.status === 'failed' ? '#A03030' : '#6B7078',
      sentBody: (() => {
        const first = String(s.name || '').trim().split(/\\s+/)[0];
        return (first ? 'Thank you, ' + first + '. ' : 'Thank you. ')
          + 'We will come back to you shortly with a slot for your working session.';
      })(),""" + s[old_end:]

    # the submit, renamed and sending the same payload the home form sends
    i = s.index("      submit: e => {")
    j = s.index("      submitLabel:", i)
    s = s[:i] + """      submitForm: e => {
        e.preventDefault();
        const need = ['name', 'email', 'phone', 'country', 'company', 'useCase'];
        const invalid = need.filter(k => !String(s[k] || '').trim());
        const email = String(s.email || '').trim();
        if (email && !/^[^@\\s]+@[^@\\s]+\\.[^@\\s]{2,}$/.test(email) && invalid.indexOf('email') === -1) {
          invalid.push('email');
        }
        if (invalid.length) {
          this.setState({ invalid: invalid, status: 'error' });
          const el = document.getElementById(
            'sp-' + (invalid[0] === 'useCase' ? 'usecase' : invalid[0]));
          if (el) { el.focus(); el.scrollIntoView({ block: 'center' }); }
          return;
        }
        this.setState({ invalid: [], status: 'sending' });
        fetch('/api/contact', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: s.name, email: s.email, phone: s.phone, country: s.country,
            company: s.company, useCase: s.useCase, model: s.model, message: s.message
          })
        })
          .then(r => { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
          .then(() => this.setState({ sent: true, status: 'sent' }))
          .catch(() => this.setState({ status: 'failed' }));
      },
""" + s[j:]

    s = s.replace("submitLabel: s.sent ? 'Opening your mail client' : 'Book a working session',",
                  "submitLabel: s.status === 'sending' ? 'Sending...'\n"
                  "        : s.sent ? 'Request received' : 'Book the working session',")

    # note -> formNote, matching the copied markup and the home wording
    # note is the last key in the returned object, so it terminates with the
    # closing brace rather than a comma - splicing on ",\n" walked off the end
    i = s.find("      note: s.sent")
    if i != -1:
        k = s.index("\n    };", i)
        s = s[:i] + """      formNote: s.sent
        ? 'Thank you \u2014 we have it, and we will come back to you to book the session.'
        : s.status === 'failed'
          ? 'That did not send. Email team@sapientpriors.com and we will pick it up.'
          : ''""" + s[k:]

    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("  TryIt.dc.html  form copied verbatim from the home page")


# The founders block under the contact form ships an empty 2.35:1 placeholder
# with a picture-icon SVG in it. The export has no slot for a real photo, so the
# swap has to happen here or the placeholder comes back on every re-export.
PLACEHOLDER_HEAD = (
    '<div style="display:flex;width:100%;aspect-ratio:2.35/1;'
    'background:rgba(132,81,46,.06);border-bottom:1px solid #EFEFEC">'
)
FOUNDER_IMG = (
    '<img src="art/people/founders.webp" '
    'alt="The SapientPriors co-founders in front of the Golden Gate Bridge" '
    'width="860" height="366" loading="lazy" decoding="async" '
    'style="width:100%;height:100%;object-fit:cover;object-position:50% 38%;display:block">'
)


def founder_photo(out):
    """Replace the founders picture-icon placeholder with the real photo."""
    for name in ("index.html", "SapientPriors.dc.html"):
        p = os.path.join(out, name)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        i = s.find(PLACEHOLDER_HEAD)
        if i == -1:
            continue
        # The placeholder is one centring div wrapping one <svg>; replace the
        # whole inner run up to the matching close of the aspect-ratio div.
        j = s.index("</svg></div></div>", i) + len("</svg></div></div>")
        s = s[:i] + PLACEHOLDER_HEAD + FOUNDER_IMG + "</div>" + s[j:]
        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
        print(f"  {name}  founders placeholder -> art/people/founders.webp")
