import streamlit as st
import requests

st.set_page_config(page_title="CliniQ - Portail Médical", page_icon="🩺")

# Initialisation du stockage du Token
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def auth_page():
    st.title("CliniQ - Portail Médical")
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])
    
    with tab1:
        # FastAPI utilise 'username' (qui peut être l'email selon ta config)
        username = st.text_input("Nom d'utilisateur", key="l_user")
        password = st.text_input("Mot de passe", type="password", key="l_pwd")
        
        if st.button("Se connecter"):
            # Format attendu par OAuth2PasswordRequestForm : data={...}
            payload = {"username": username, "password": password}
            try:
                res = requests.post("http://backend:8000/auth/login", data=payload)
                if res.status_code == 200:
                    token_data = res.json()
                    st.session_state.access_token = token_data["access_token"]
                    st.session_state.authenticated = True
                    st.session_state.user_name = username
                    st.success("Authentification réussie !")
                    st.rerun()
                else:
                    st.error(f"Échec : {res.json().get('detail')}")
            except Exception as e:
                st.error(f"Erreur de connexion : {e}")

    with tab2:
        # Sign up (utilise ton endpoint /auth/signup)
        new_user = st.text_input("Username")
        new_email = st.text_input("Email")
        new_pwd = st.text_input("Password", type="password")
        if st.button("Créer mon compte"):
            user_data = {"username": new_user, "email": new_email, "password": new_pwd}
            res = requests.post("http://backend:8000/auth/signup", json=user_data)
            if res.status_code == 200:
                st.success("Compte créé ! Connectez-vous maintenant.")
            else:
                st.error(f"Erreur : {res.json().get('detail')}")

if not st.session_state.authenticated:
    auth_page()
else:
    st.sidebar.success(f"Dr. {st.session_state.user_name}")
    st.title("Tableau de Bord CliniQ")
    st.info("Utilisez la barre latérale pour accéder aux services.")
    if st.sidebar.button("Déconnexion"):
        st.session_state.access_token = None
        st.session_state.authenticated = False
        st.rerun()