import { Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { VendorLogo, ScorePill, EvidenceChip } from '@/components/custom'

/**
 * UI Kit - Design System Style Guide
 * Displays all UI components for reference and testing
 */
export function UIKit() {
    return (
        <div className="p-6 space-y-10 max-w-4xl mx-auto">
            <div>
                <h1 className="text-display-lg font-display font-bold mb-2">UI Kit</h1>
                <p className="text-muted-foreground">
                    Procurely design system components and patterns
                </p>
            </div>

            {/* Typography */}
            <section>
                <h2 className="text-heading font-semibold mb-4">Typography</h2>
                <Card>
                    <CardContent className="p-6 space-y-4">
                        <p className="text-display-lg font-display font-bold">Display Large (48px)</p>
                        <p className="text-display font-display font-bold">Display (36px)</p>
                        <p className="text-heading font-semibold">Heading (24px)</p>
                        <p className="text-subheading font-semibold">Subheading (18px)</p>
                        <p className="text-base">Body (16px)</p>
                        <p className="text-sm text-muted-foreground">Caption (14px)</p>
                        <p className="text-xs text-muted-foreground">Small (12px)</p>
                    </CardContent>
                </Card>
            </section>

            {/* Buttons */}
            <section>
                <h2 className="text-heading font-semibold mb-4">Buttons</h2>
                <Card>
                    <CardContent className="p-6 flex flex-wrap gap-3">
                        <Button variant="default">Default</Button>
                        <Button variant="gradient">Gradient</Button>
                        <Button variant="secondary">Secondary</Button>
                        <Button variant="outline">Outline</Button>
                        <Button variant="ghost">Ghost</Button>
                        <Button variant="destructive">Destructive</Button>
                        <Button variant="link">Link</Button>
                        <Button disabled>Disabled</Button>
                    </CardContent>
                </Card>
            </section>

            {/* Cards */}
            <section>
                <h2 className="text-heading font-semibold mb-4">Cards</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Standard Card</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-muted-foreground">
                                Cards provide a container for content with hover effects
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="glass-card">
                        <CardHeader>
                            <CardTitle>Glass Card</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-muted-foreground">
                                Glassmorphism effect for premium feel
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </section>

            {/* Custom Components */}
            <section>
                <h2 className="text-heading font-semibold mb-4">Custom Components</h2>
                <Card>
                    <CardContent className="p-6 space-y-6">
                        {/* Vendor Logos */}
                        <div>
                            <h3 className="text-sm font-medium mb-3">VendorLogo</h3>
                            <div className="flex items-center gap-4">
                                <VendorLogo name="Acme Corp" size="sm" />
                                <VendorLogo name="Global Supply" size="md" />
                                <VendorLogo name="PT Indonesia Jaya" size="lg" />
                                <VendorLogo name="XYZ Trading" size="xl" />
                            </div>
                        </div>

                        {/* Score Pills */}
                        <div>
                            <h3 className="text-sm font-medium mb-3">ScorePill</h3>
                            <div className="flex items-center gap-4">
                                <ScorePill label="Fit" score={92} tooltipText="Strong match for requirements" />
                                <ScorePill label="Trust" score={65} tooltipText="Moderate evidence quality" />
                                <ScorePill label="Risk" score={28} tooltipText="Low risk score" />
                            </div>
                        </div>

                        {/* Evidence Chips */}
                        <div>
                            <h3 className="text-sm font-medium mb-3">EvidenceChip</h3>
                            <div className="flex flex-wrap items-center gap-2">
                                <EvidenceChip sourceType="official" />
                                <EvidenceChip sourceType="directory" />
                                <EvidenceChip sourceType="marketplace" />
                                <EvidenceChip sourceType="document" />
                                <EvidenceChip sourceType="other" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </section>

            {/* States */}
            <section>
                <h2 className="text-heading font-semibold mb-4">States</h2>
                <Card>
                    <CardContent className="p-6 space-y-6">
                        {/* Loading Skeleton */}
                        <div>
                            <h3 className="text-sm font-medium mb-3">Skeleton Loaders</h3>
                            <div className="space-y-3">
                                <div className="skeleton h-4 w-3/4" />
                                <div className="skeleton h-4 w-1/2" />
                                <div className="skeleton h-10 w-full rounded-xl" />
                            </div>
                        </div>

                        {/* Score Badges */}
                        <div>
                            <h3 className="text-sm font-medium mb-3">Score Badges</h3>
                            <div className="flex items-center gap-3">
                                <span className="px-3 py-1 rounded-full text-sm font-medium score-high">High (70%+)</span>
                                <span className="px-3 py-1 rounded-full text-sm font-medium score-medium">Medium (40-69%)</span>
                                <span className="px-3 py-1 rounded-full text-sm font-medium score-low">Low (&lt;40%)</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </section>

            {/* Colors */}
            <section>
                <h2 className="text-heading font-semibold mb-4">Brand Colors</h2>
                <Card>
                    <CardContent className="p-6">
                        <div className="grid grid-cols-5 gap-2">
                            {[50, 100, 200, 300, 400, 500, 600, 700, 800, 900].map((shade) => (
                                <div key={shade} className="text-center">
                                    <div
                                        className={`h-12 rounded-lg bg-brand-${shade} mb-1`}
                                        style={{
                                            backgroundColor: `var(--tw-colors-brand-${shade}, hsl(207, 91%, ${100 - shade / 10}%))`
                                        }}
                                    />
                                    <span className="text-xs">{shade}</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </section>
        </div>
    )
}

export default UIKit
