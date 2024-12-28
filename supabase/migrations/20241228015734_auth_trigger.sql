CREATE TRIGGER on_new_auth_user_create_profile AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION create_profile();


