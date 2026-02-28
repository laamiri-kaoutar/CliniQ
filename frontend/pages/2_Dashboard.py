import streamlit as st
import requests

st.set_page_config(page_title="Mon Historique", page_icon="📊")

if not st.session_state.get("authenticated"):
    st.warning("Veuillez vous connecter.")
    st.stop()

st.title("Historique des Interactions")

# On prépare le header avec le Token
headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

try:
    response = requests.get("http://backend:8000/chat/history", headers=headers)
    if response.status_code == 200:
        history = response.json()
        if not history:
            st.write("Aucune donnée enregistrée.")
        for item in reversed(history):
            # Debug temporaire pour voir les vrais noms des clés
            # st.write(item.keys()) 
            
            # On récupère la question (vérifie si c'est 'query_text' ou 'query')
            q = item.get('query_text') or item.get('query') or "Question inconnue"
            
            # On récupère la réponse (vérifie si c'est 'answer' ou 'response_text')
            a = item.get('answer') or item.get('response_text') or "Pas de réponse"
            
            with st.expander(f"Question : {q}"):
                st.write(f"**Réponse :** {a}")
                st.caption(f"Fidélité : {item.get('faithfulness_score', 'N/A')}")
    else:
        st.error(f"Erreur {response.status_code} : {response.text}")
except Exception as e:
    st.error(f"Erreur de connexion : {e}")