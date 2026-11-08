/**
 * Connecteur Backend Django / MySQL pour l'interface existante EauSolidaire.
 * Conserve à 100 % le design, le HTML, le CSS et les interactions visuelles d'origine,
 * tout en remplaçant la persistance locale en mémoire par les vraies tables MySQL via fetch() + CSRF.
 */
(function () {
  function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  async function apiPost(url, payload) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        credentials: 'same-origin',
        body: JSON.stringify(payload || {}),
      });
      return await res.json();
    } catch (err) {
      return { ok: false, error: 'Erreur de communication avec le serveur.' };
    }
  }

  D.equipements = D.equipements || [];

  async function syncFromBackend() {
    try {
      const res = await fetch('/api/state/', { credentials: 'same-origin' });
      const data = await res.json();
      if (data && data.ok && data.D) {
        D.villages = data.D.villages || D.villages;
        D.pts = data.D.pts || D.pts;
        D.equipements = data.D.equipements || D.equipements;
        D.pannes = data.D.pannes || D.pannes;
        D.stock = data.D.stock || D.stock;
        D.hist = data.D.hist || D.hist;
        D.notifs = data.D.notifs || D.notifs;
        D.techs = data.D.techs || D.techs;
        if (data.U && !U) {
          U = data.U;
        }
        route();
      }
    } catch (e) {
      // Conservation transparente des données affichées si hors-ligne
    }
  }

  // 1. Interception du formulaire de connexion (#lf) en phase capture
  document.addEventListener(
    'submit',
    async function (e) {
      if (e.target && e.target.id === 'lf') {
        e.preventDefault();
        e.stopImmediatePropagation();
        const uInput = e.target.u ? e.target.u.value.trim() : '';
        const pInput = e.target.p ? e.target.p.value : '';
        const res = await apiPost('/api/auth/login/', { u: uInput, p: pInput });
        if (res && res.ok && res.user) {
          U = res.user;
          view = U.role === 'admin' ? 'over' : 'home';
          await syncFromBackend();
          location.hash = U.role;
          toast('Connecté : ' + U.name);
        } else {
          toast((res && res.error) || 'Identifiants incorrects');
        }
      }
    },
    true
  );

  // 2. Déconnexion Django lors du clic sur Déconnexion + Réinitialisation de mot de passe par e-mail SMTP
  document.addEventListener(
    'click',
    function (e) {
      const a = e.target.closest('aside.side2 a');
      if (a && a.textContent.includes('Déconnexion')) {
        apiPost('/api/auth/logout/', {});
        return;
      }
      const resetLink = e.target.closest('a[onclick*="Réinitialisation"]');
      if (resetLink) {
        e.preventDefault();
        e.stopImmediatePropagation();
        window.openPasswordResetModal();
      }
    },
    true
  );

  window.openPasswordResetModal = function () {
    modal(
      `<h3>Mot de passe oublié</h3><p class="mut">Saisissez votre adresse e-mail ou votre identifiant pour recevoir un lien de réinitialisation par e-mail SMTP.</p><form><label>Adresse e-mail ou identifiant</label><input name="email" required placeholder="exemple@domaine.com"><p><button class="btn" style="width:100%">Envoyer le lien par e-mail</button></p><p style="text-align:center"><button type="button" class="btn alt sm" onclick="openPasswordResetConfirmModal('','')">J’ai déjà un code de réinitialisation</button></p></form>`,
      (d) => {
        apiPost('/api/auth/password-reset/', { email: d.email }).then((res) => {
          toast((res && (res.message || res.error)) || 'Demande envoyée');
        });
      }
    );
  };

  window.openPasswordResetConfirmModal = function (uidPrefill, tokenPrefill) {
    modal(
      `<h3>Nouveau mot de passe</h3><form><label>Identifiant (UID)</label><input name="uid" required value="${esc(
        uidPrefill || ''
      )}"><label>Jeton de sécurité (Token)</label><input name="token" required value="${esc(
        tokenPrefill || ''
      )}"><label>Nouveau mot de passe (8 caractères min.)</label><input name="password" type="password" minlength="8" required><label>Confirmer le mot de passe</label><input name="password2" type="password" minlength="8" required><p><button class="btn" style="width:100%">Enregistrer le mot de passe</button></p></form>`,
      (d) => {
        if (d.password !== d.password2) {
          toast('Les deux mots de passe ne correspondent pas');
          return false;
        }
        if (d.password.length < 8) {
          toast('Le mot de passe doit contenir au moins 8 caractères');
          return false;
        }
        apiPost('/api/auth/password-reset/confirm/', {
          uid: d.uid,
          token: d.token,
          password: d.password,
        }).then((res) => {
          if (res && res.ok) {
            toast(res.message || 'Mot de passe mis à jour avec succès');
            if (location.search.includes('token=')) {
              history.replaceState(null, '', location.pathname + '#connexion');
            }
          } else {
            toast((res && res.error) || 'Lien ou jeton invalide');
          }
        });
      }
    );
  };

  // 3. Notifications : marquer tout comme lu côté MySQL
  window.notifs = function () {
    modal(
      `<h3>Notifications</h3>${
        D.notifs.map((n) => `<p>• ${esc(n)}</p>`).join('') ||
        '<p class="mut">Aucune notification.</p>'
      }<button class="btn" onclick="clearNotifsBackend()">Tout marquer comme lu</button>`
    );
  };
  window.clearNotifsBackend = async function () {
    D.notifs = [];
    closeM();
    await apiPost('/api/auth/notifications/clear/', {});
    route();
  };

  // 4. Gestion géographique : Ajout et Suppression de village dans MySQL
  window.addV = function () {
    modal(
      `<h3>Nouveau village</h3><form><label>Village</label><input name="n" required><label>Commune</label><input name="c" required><label>Cercle</label><input name="ce" required><label>Région</label><input name="r" required><p><button class="btn">Enregistrer</button></p></form>`,
      (d) => {
        D.villages.push(d);
        toast('Village ajouté');
        geo($('#c'));
        apiPost('/api/localisation/villages/add/', d).then((res) => {
          if (res && !res.ok && res.error) {
            toast(res.error);
          }
          syncFromBackend();
        });
      }
    );
  };

  window.delV = async function (i) {
    const v = D.villages[i];
    if (!v) return;
    if (D.pts.some((p) => p.v == v.n)) {
      return toast('Suppression impossible : des points d’eau en dépendent');
    }
    if (confirm('Supprimer ' + v.n + ' ?')) {
      const res = await apiPost('/api/localisation/villages/delete/', { n: v.n, id: v.id });
      if (res && !res.ok) {
        return toast(res.error || 'Suppression impossible');
      }
      D.villages.splice(i, 1);
      toast('Supprimé');
      if (typeof fl === 'function') fl();
    }
  };

  // 5. Points d'eau et Équipements installés : Ajout, changement d'état, suppression et mise à jour GPS dans MySQL
  window.pts = function (c) {
    c.innerHTML =
      `<h2>Points d’eau</h2><div class="tools"><input id="q" placeholder="Rechercher…" oninput="fl()"><select id="s" onchange="fl()"><option value="">Tous les états</option>${ST.map(
        (s) => `<option>${s}</option>`
      ).join('')}</select><button class="btn" onclick="addP()">Ajouter</button></div>` +
      table(['Réf.', 'Nom', 'Type', 'Village', 'État', 'Changer l’état', 'Carte'], '', 'tb') +
      `<h3 style="margin-top:20px">Équipements installés sur les points d’eau</h3><div class="tools"><input id="qeq" placeholder="Rechercher un équipement…" oninput="fl()"><button class="btn" onclick="addEq()">Ajouter un équipement</button></div>` +
      table(
        ['Réf.', 'Nom', 'Type', 'Point d’eau', 'État', 'Changer l’état', ''],
        '',
        'tb-eq'
      );

    fl = () => {
      const q = ($('#q')?.value || '').toLowerCase(),
        s = $('#s')?.value || '';
      if ($('#tb')) {
        $('#tb').innerHTML =
          D.pts
            .map((p, i) => ({ p, i }))
            .filter((o) => (!s || o.p.s == s) && JSON.stringify(o.p).toLowerCase().includes(q))
            .map(
              ({ p, i }) =>
                `<tr><td>${p.ref}</td><td>${esc(p.n)}</td><td>${p.t}</td><td>${esc(
                  p.v
                )}</td><td>${badge(p.s)}</td><td><select onchange="setS(${i},this.value)">${ST.map(
                  (x) => `<option ${x == p.s ? 'selected' : ''}>${x}</option>`
                ).join(
                  ''
                )}</select></td><td><button class="btn alt sm" onclick="view='map';SEL='${
                  p.ref
                }';route()">${p.la != null ? 'Localiser' : 'Sans position'}</button></td></tr>`
            )
            .join('') || '<tr><td colspan=7 class="mut">Aucun résultat.</td></tr>';
      }
      const qeq = ($('#qeq')?.value || '').toLowerCase();
      if ($('#tb-eq')) {
        $('#tb-eq').innerHTML =
          (D.equipements || [])
            .map((e, i) => ({ e, i }))
            .filter((o) => JSON.stringify(o.e).toLowerCase().includes(qeq))
            .map(
              ({ e, i }) =>
                `<tr><td>${esc(e.ref)}</td><td>${esc(e.nom)}</td><td>${esc(
                  e.type
                )}</td><td>${esc(e.pt)} (${esc(e.pt_nom || '')})</td><td>${badge(
                  e.etat
                )}</td><td><select onchange="setEqS(${i},this.value)">${ST.map(
                  (x) => `<option ${x == e.etat ? 'selected' : ''}>${x}</option>`
                ).join(
                  ''
                )}</select></td><td><button class="btn alt sm" onclick="delEq(${i})">Supprimer</button></td></tr>`
            )
            .join('') || '<tr><td colspan=7 class="mut">Aucun équipement enregistré.</td></tr>';
      }
    };
    fl();
  };

  window.addEq = function () {
    modal(
      `<h3>Nouvel équipement</h3><form><label>Référence</label><input name="ref" required placeholder="EQ-003"><label>Nom de l’équipement</label><input name="nom" required placeholder="Pompe Vergnet HPV 60"><label>Type d’équipement</label><select name="type"><option>Pompe manuelle</option><option>Pompe solaire</option><option>Pompe immergée</option><option>Château d'eau / Réservoir</option><option>Panneau solaire</option><option>Robinet / Borne</option><option>Autre</option></select><label>Point d’eau associé</label><select name="pt">${D.pts
        .map((p) => `<option value="${esc(p.ref)}">${esc(p.ref)} · ${esc(p.n)}</option>`)
        .join('')}</select><label>État initial</label><select name="etat">${ST.map(
        (s) => `<option>${s}</option>`
      ).join('')}</select><label>Description (facultative)</label><input name="description"><p><button class="btn">Enregistrer</button></p></form>`,
      (d) => {
        if ((D.equipements || []).some((e) => e.ref == d.ref)) {
          toast('Référence équipement déjà utilisée');
          return false;
        }
        const ptObj = D.pts.find((p) => p.ref == d.pt);
        D.equipements.push({
          ref: d.ref,
          nom: d.nom,
          type: d.type,
          pt: d.pt,
          pt_nom: ptObj ? ptObj.n : '',
          etat: d.etat,
          description: d.description || '',
        });
        toast('Équipement ajouté');
        pts($('#c'));
        apiPost('/api/equipements/add/', d).then((res) => {
          if (res && !res.ok && res.error) toast(res.error);
          syncFromBackend();
        });
      }
    );
  };

  window.setEqS = async function (i, v) {
    const eq = (D.equipements || [])[i];
    if (!eq) return;
    eq.etat = v;
    if (typeof fl === 'function') fl();
    toast('État de l’équipement mis à jour');
    await apiPost('/api/equipements/etat/', { id: eq.id, ref: eq.ref, etat: v });
    syncFromBackend();
  };

  window.delEq = async function (i) {
    const eq = (D.equipements || [])[i];
    if (!eq) return;
    if (confirm('Supprimer l’équipement ' + eq.nom + ' (' + eq.ref + ') ?')) {
      const res = await apiPost('/api/equipements/delete/', { id: eq.id, ref: eq.ref });
      if (res && !res.ok) {
        return toast(res.error || 'Suppression impossible');
      }
      D.equipements.splice(i, 1);
      toast('Équipement supprimé');
      if (typeof fl === 'function') fl();
    }
  };

  window.pick = function (ref) {
    SEL = ref;
    const el = $('#mpan');
    if (!el) return;
    const p = D.pts.find((x) => x.ref == ref),
      v = D.villages.find((x) => x.n == p.v) || {},
      ps = D.pannes.filter((n) => n.pt == ref),
      eqs = (D.equipements || []).filter((e) => e.pt == ref);
    el.innerHTML = `<h3>${p.ref} · ${esc(p.n)}</h3>${badge(p.s)}<p class="mut">${
      p.t
    } · ${esc(p.v)}, commune de ${esc(v.c || '')}, cercle de ${esc(
      v.ce || ''
    )}, région de ${esc(v.r || '')}</p>${
      p.la != null
        ? `<p><b>Position</b> ${p.la.toFixed(4)}° N, ${Math.abs(p.lo).toFixed(4)}° ${
            p.lo < 0 ? 'O' : 'E'
          }<br><a href="https://www.openstreetmap.org/?mlat=${p.la}&mlon=${
            p.lo
          }#map=14/${p.la}/${p.lo}" target="_blank" rel="noopener"><u>Voir sur OpenStreetMap</u></a></p>`
        : '<p class="mut">Position GPS non renseignée.</p>'
    }<h3>Équipements installés</h3>${
      eqs.map((e) => `<p>${esc(e.ref)} · ${esc(e.nom)} (${esc(e.type)}) ${badge(e.etat)}</p>`).join('') ||
      '<p class="mut">Aucun équipement rattaché.</p>'
    }<h3>Suivi de l’état</h3>${p.log
      .map((l) => `<p>${l.d} · ${l.s ? badge(l.s) : ''} ${esc(l.n || '')}</p>`)
      .join('')}<h3>Pannes et interventions</h3>${
      ps
        .map((n) => `<p>${esc(n.d)}<br>${badge(n.s)} ${n.tech ? '· ' + esc(n.tech) : ''}</p>`)
        .join('') || '<p class="mut">Aucune panne enregistrée.</p>'
    }<p>${
      U.role != 'local'
        ? `<button class="btn sm" onclick="setPos('${ref}')">${
            p.la != null ? 'Modifier' : 'Renseigner'
          } la position</button>`
        : `<button class="btn sm" onclick="view='dec';route()">Déclarer une panne</button>`
    }</p>`;
    el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  };

  window.addP = function () {
    modal(
      `<h3>Nouveau point d’eau</h3><form><label>Référence</label><input name="ref" required><label>Nom</label><input name="n" required><label>Type</label><select name="t"><option>Forage</option><option>Puits</option><option>Autre</option></select><label>Village</label><select name="v">${D.villages
        .map((v) => `<option>${esc(v.n)}</option>`)
        .join('')}</select><label>Latitude (facultatif)</label><input name="la" type="number" step="any"><label>Longitude (facultatif)</label><input name="lo" type="number" step="any"><p><button type="button" class="btn alt sm" onclick="gps()">Utiliser ma position</button></p><p><button class="btn">Enregistrer</button></p></form>`,
      (d) => {
        if (D.pts.some((p) => p.ref == d.ref)) {
          toast('Référence déjà utilisée');
          return false;
        }
        d.la = d.la === '' ? null : +d.la;
        d.lo = d.lo === '' ? null : +d.lo;
        if ((d.la != null || d.lo != null) && !okPos(d.la, d.lo)) {
          toast('Position invalide : latitude 10 à 25, longitude −12,5 à 4,4');
          return false;
        }
        d.s = 'Fonctionnel';
        d.log = [{ d: today(), s: 'Fonctionnel', n: 'Création' }];
        D.pts.push(d);
        toast('Point d’eau ajouté');
        pts($('#c'));
        apiPost('/api/points-eau/add/', d).then((res) => {
          if (res && !res.ok && res.error) toast(res.error);
          syncFromBackend();
        });
      }
    );
  };

  window.setS = async function (i, v) {
    const p = D.pts[i];
    if (!p) return;
    p.s = v;
    p.log.unshift({ d: today(), s: v });
    if (typeof fl === 'function') fl();
    toast('État mis à jour');
    await apiPost('/api/points-eau/etat/', { ref: p.ref, s: v });
    syncFromBackend();
  };

  window.setPos = function (ref) {
    const p = D.pts.find((x) => x.ref == ref);
    if (!p) return;
    modal(
      `<h3>Position de ${p.ref}</h3><form><label>Latitude</label><input name="la" type="number" step="any" required value="${
        p.la ?? ''
      }"><label>Longitude</label><input name="lo" type="number" step="any" required value="${
        p.lo ?? ''
      }"><p><button type="button" class="btn alt sm" onclick="gps()">Utiliser ma position</button></p><p><button class="btn">Enregistrer</button></p></form>`,
      (x) => {
        const a = +x.la,
          o = +x.lo;
        if (!okPos(a, o)) {
          toast('Position invalide : latitude 10 à 25, longitude −12,5 à 4,4');
          return false;
        }
        p.la = a;
        p.lo = o;
        p.log.unshift({ d: today(), n: 'Position mise à jour' });
        toast('Position enregistrée');
        mapV($('#c'));
        apiPost('/api/points-eau/position/', { ref: p.ref, la: a, lo: o }).then(() =>
          syncFromBackend()
        );
      }
    );
  };

  // 6. Pannes et Interventions : Déclaration, Affectation, Démarrage, Clôture
  window.setP = async function (i, s) {
    const p = D.pannes[i];
    if (!p) return;
    p.s = s;
    toast('Statut : ' + s);
    pan($('#c'));
    await apiPost('/api/pannes/statut/', { id: p.id, s: s });
    syncFromBackend();
  };

  window.aff = function (i) {
    const p = D.pannes[i];
    if (!p) return;
    modal(
      `<h3>Affecter un technicien</h3><form><select name="t">${D.techs
        .map((t) => `<option>${t}</option>`)
        .join('')}</select><p><button class="btn">Affecter</button></p></form>`,
      (d) => {
        p.tech = d.t;
        p.s = 'Technicien affecté';
        toast('Intervention créée pour ' + d.t);
        pan($('#c'));
        apiPost('/api/interventions/affecter/', { id: p.id, t: d.t }).then(() =>
          syncFromBackend()
        );
      }
    );
  };

  window.dec = function (c) {
    const villagePts = D.pts.filter((p) => p.v == U.village);
    const firstPtRef = villagePts[0] ? villagePts[0].ref : '';
    const renderEqOptions = (ptRef) =>
      `<option value="">Aucun équipement spécifique</option>` +
      (D.equipements || [])
        .filter((e) => e.pt == ptRef)
        .map((e) => `<option value="${esc(e.ref)}">${esc(e.ref)} · ${esc(e.nom)}</option>`)
        .join('');

    c.innerHTML = `<h2>Déclarer une panne</h2><form class="card" style="max-width:480px" id="df"><label>Point d’eau</label><select name="pt" id="df-pt">${villagePts
      .map((p) => `<option>${p.ref}</option>`)
      .join(
        ''
      )}</select><label>Équipement concerné (facultatif)</label><select name="eq" id="df-eq">${renderEqOptions(
      firstPtRef
    )}</select><label>Description</label><textarea name="d" required></textarea><label>Priorité</label><select name="p"><option>Faible</option><option>Moyenne</option><option>Élevée</option><option>Critique</option></select><label>Photo (facultative)</label><input type="file" name="photo" accept="image/*"><p><button class="btn">Envoyer le signalement</button></p></form>`;
    const ptSelect = $('#df-pt');
    if (ptSelect) {
      ptSelect.onchange = () => {
        const eqSelect = $('#df-eq');
        if (eqSelect) eqSelect.innerHTML = renderEqOptions(ptSelect.value);
      };
    }
    $('#df').onsubmit = async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const d = Object.fromEntries(formData);
      formData.append('by', U.name);
      try {
        await fetch('/api/pannes/add/', {
          method: 'POST',
          headers: { 'X-CSRFToken': getCsrfToken() },
          credentials: 'same-origin',
          body: formData,
        });
      } catch (err) {}
      D.pannes.push({
        id: Date.now(),
        pt: d.pt,
        d: d.d,
        p: d.p,
        s: 'Nouveau signalement',
        by: U.name,
        tech: '',
      });
      D.notifs.push('Nouveau signalement : ' + d.pt);
      toast('Signalement envoyé');
      view = 'mes';
      await syncFromBackend();
      route();
    };
  };

  window.setP2 = async function (i, s) {
    const p = D.pannes[i];
    if (!p) return;
    p.s = s;
    D.notifs.push('Statut modifié : ' + p.pt);
    toast('Intervention démarrée');
    techHome($('#c'));
    await apiPost('/api/interventions/demarrer/', { id: p.id, s: s });
    syncFromBackend();
  };

  window.fin = function (i) {
    const p = D.pannes[i];
    if (!p) return;
    modal(
      `<h3>Terminer l’intervention</h3><form><label>Compte rendu</label><textarea name="r" required></textarea><label>Pièce utilisée</label><select name="pc"><option value="">Aucune</option>${D.stock
        .map((s, j) => `<option value="${j}">${esc(s.n)} (${s.q})</option>`)
        .join(
          ''
        )}</select><label>Quantité</label><input name="q" type="number" min="1" value="1"><p><button class="btn">Terminer</button></p></form>`,
      (d) => {
        let pieceRef = '';
        if (d.pc !== '') {
          const s = D.stock[+d.pc];
          if (+d.q > s.q) {
            toast('Stock insuffisant');
            return false;
          }
          pieceRef = s.ref;
          s.q -= +d.q;
          D.hist.unshift('−' + d.q + ' ' + s.n + ' (intervention ' + p.pt + ')');
          if (s.q <= s.min) D.notifs.push('Stock faible : ' + s.n);
        }
        p.s = 'Résolu';
        D.notifs.push('Intervention terminée : ' + p.pt);
        toast('Intervention terminée');
        techHome($('#c'));
        apiPost('/api/interventions/terminer/', {
          id: p.id,
          r: d.r,
          piece_ref: pieceRef,
          q: +d.q || 1,
        }).then(() => syncFromBackend());
      }
    );
  };

  // 7. Stock : Entrées et sorties de pièces détachées dans MySQL
  window.mv = function (i, s) {
    const item = D.stock[i];
    if (!item) return;
    modal(
      `<h3>${s > 0 ? 'Entrée' : 'Sortie'} : ${esc(
        item.n
      )}</h3><form><label>Quantité</label><input name="q" type="number" min="1" required><p><button class="btn">Valider</button></p></form>`,
      (d) => {
        const q = +d.q;
        if (s < 0 && q > item.q) {
          toast('Stock insuffisant : ' + item.q + ' disponible(s)');
          D.notifs.push('Stock insuffisant : ' + item.n);
          return false;
        }
        item.q += s * q;
        D.hist.unshift((s > 0 ? '+' : '−') + q + ' ' + item.n);
        if (item.q <= item.min) D.notifs.push('Stock faible : ' + item.n);
        toast('Mouvement enregistré');
        stk($('#c'));
        apiPost('/api/stock/mouvement/', { ref: item.ref, s: s, q: q }).then(() =>
          syncFromBackend()
        );
      }
    );
  };

  // 8. Formulaire de contact public connecté à MySQL
  window.cSend = function (e) {
    e.preventDefault();
    const f = e.target;
    const ok = [...f.querySelectorAll('input[name=nom],input[name=email],textarea')]
      .map(cVal)
      .every(Boolean);
    if (!ok) {
      toast('Vérifiez les champs en rouge');
      return false;
    }
    const b = f.querySelector('.send');
    b.disabled = true;
    b.textContent = 'Envoi en cours…';
    const payload = {
      sj: f.sj.value,
      nom: f.nom.value.trim(),
      email: f.email.value.trim(),
      msg: f.msg.value.trim(),
    };
    apiPost('/api/auth/contact/', payload).then(() => {
      $('#cr').innerHTML = `<div class="okm"><div class="ck">✓</div><h3>Merci ${esc(
        payload.nom.split(' ')[0]
      )} !</h3><p class="mut">Votre message « ${esc(
        payload.sj
      )} » a bien été enregistré par le serveur.</p><button class="btn alt" onclick="cReset()">Nouveau message</button></div>`;
    });
    return false;
  };

  // Chargement initial des données depuis MySQL au démarrage
  syncFromBackend();

  // Ouverture automatique de la modale de confirmation de nouveau mot de passe si lien e-mail (?uid=...&token=...)
  const params = new URLSearchParams(location.search);
  if (params.get('uid') && params.get('token')) {
    location.hash = 'connexion';
    setTimeout(() => {
      window.openPasswordResetConfirmModal(params.get('uid'), params.get('token'));
    }, 250);
  }
})();
