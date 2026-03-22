import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

function Spinner({ className }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("inline-block", className)}>
      <div className="relative h-8 w-8 animate-spin">
        <div className="absolute inset-0 rounded-full border-2 border-border" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary" />
      </div>
    </div>
  )
}

export { Skeleton, Spinner }
