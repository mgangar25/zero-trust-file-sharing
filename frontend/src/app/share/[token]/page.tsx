import { PublicShareClient } from "@/components/share/PublicShareClient";

type SharePageProps = {
  params: Promise<{
    token: string;
  }>;
};

export default async function SharePage({ params }: SharePageProps) {
  const { token } = await params;

  return <PublicShareClient token={token} />;
}
