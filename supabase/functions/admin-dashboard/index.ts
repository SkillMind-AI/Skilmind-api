import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "https://skillmind-ai.github.io",
  "Access-Control-Allow-Headers":
    "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

Deno.serve(async (req: Request) => {
  const respond = (data: unknown, status = 200) =>
    new Response(JSON.stringify(data), {
      status,
      headers: {
        ...corsHeaders,
        "Content-Type": "application/json",
      },
    });

  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return respond({ error: "Method not allowed" }, 405);
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const anonKey = Deno.env.get("SUPABASE_ANON_KEY");
  const adminKey = Deno.env.get("ADMIN_SERVICE_KEY");
  const adminEmail = (
    Deno.env.get("ADMIN_EMAIL") || ""
  ).trim().toLowerCase();

  if (!supabaseUrl || !anonKey || !adminKey || !adminEmail) {
    return respond({
      error: "Server configuration is incomplete",
    }, 500);
  }

  const authHeader = req.headers.get("Authorization");

  if (!authHeader?.startsWith("Bearer ")) {
    return respond({ error: "Please log in first" }, 401);
  }

  const userClient = createClient(supabaseUrl, anonKey, {
    global: {
      headers: { Authorization: authHeader },
    },
  });

  const { data: authData, error: authError } =
    await userClient.auth.getUser();

  if (authError || !authData.user) {
    return respond({ error: "Invalid login session" }, 401);
  }

  if (
    (authData.user.email || "").trim().toLowerCase() !== adminEmail
  ) {
    return respond({ error: "Admin access denied" }, 403);
  }

  const adminClient = createClient(supabaseUrl, adminKey);

  const { data, error } = await adminClient.auth.admin.listUsers({
    page: 1,
    perPage: 100,
  });

  if (error) {
    console.error("Unable to list users:", error.message);
    return respond({ error: "Unable to load users" }, 500);
  }

  const users = data.users.map((user) => ({
    email: user.email,
    registered_at: user.created_at,
    email_confirmed: Boolean(user.email_confirmed_at),
    last_sign_in: user.last_sign_in_at,
  }));

  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);

  return respond({
    total_users: data.users.length,
    confirmed_users: users.filter(
      (user) => user.email_confirmed,
    ).length,
    todays_registrations: users.filter(
      (user) => new Date(user.registered_at) >= today,
    ).length,
    users,
  });
});
