{% extends "base.html" %}

{% block title %}Accueil - NoteMaster{% endblock %}

{% block content %}
<div class="jumbotron">
    <h1 class="display-4">Bienvenue sur NoteMaster</h1>
    <p class="lead">Plateforme d'évaluation et de partage des commentaires</p>
    <hr class="my-4">
    <p>Application en cours de développement</p>
    <a class="btn btn-primary btn-lg" href="{{ url_for('public.ranking') }}">Voir le classement</a>
</div>
{% endblock %}