"use server";

import { z } from "zod";

import { createUser, getUser } from "@/lib/db/queries";

import { signIn } from "./auth";

const PASSWORD_MIN = 8;
const passwordSchema = z
  .string()
  .min(PASSWORD_MIN, { message: "min_length" })
  .regex(/[a-z]/, { message: "lowercase" })
  .regex(/[A-Z]/, { message: "uppercase" })
  .regex(/[0-9]/, { message: "number" })
  .regex(/[^A-Za-z0-9]/, { message: "special" });

const authFormSchema = z.object({
  email: z.string().email(),
  password: passwordSchema,
});

export type LoginActionState = {
  status: "idle" | "in_progress" | "success" | "failed" | "invalid_data";
};

export const login = async (
  _: LoginActionState,
  formData: FormData
): Promise<LoginActionState> => {
  try {
    const validatedData = authFormSchema.parse({
      email: formData.get("email"),
      password: formData.get("password"),
    });

    await signIn("credentials", {
      email: validatedData.email,
      password: validatedData.password,
      redirect: false,
    });

    return { status: "success" };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { status: "invalid_data" };
    }

    return { status: "failed" };
  }
};

export type RegisterActionState = {
  status:
    | "idle"
    | "in_progress"
    | "success"
    | "failed"
    | "user_exists"
    | "invalid_data"
    | "password_mismatch"
    | "weak_password";
};

export const register = async (
  _: RegisterActionState,
  formData: FormData
): Promise<RegisterActionState> => {
  try {
    const password = formData.get("password");
    const passwordConfirm = formData.get("passwordConfirm");

    const validatedData = authFormSchema.parse({
      email: formData.get("email"),
      password: formData.get("password"),
    });

    if (typeof password !== "string" || typeof passwordConfirm !== "string") {
      return { status: "invalid_data" };
    }
    if (password !== passwordConfirm) {
      return { status: "password_mismatch" };
    }

    const [user] = await getUser(validatedData.email);

    if (user) {
      return { status: "user_exists" } as RegisterActionState;
    }
    await createUser(validatedData.email, validatedData.password);
    await signIn("credentials", {
      email: validatedData.email,
      password: validatedData.password,
      redirect: false,
    });

    return { status: "success" };
  } catch (error) {
    if (error instanceof z.ZodError) {
      const hasPasswordIssue = error.issues.some((i) =>
        i.path.includes("password")
      );
      if (hasPasswordIssue) {
        return { status: "weak_password" };
      }
      return { status: "invalid_data" };
    }

    return { status: "failed" };
  }
};
