plugins {
 id("com.android.application")
 id("org.jetbrains.kotlin.android")
 id("org.jetbrains.kotlin.plugin.compose")
}
android {
 namespace = "com.blazesystems.threadharbor"
 compileSdk = 36
 defaultConfig { applicationId = "com.blazesystems.threadharbor"; minSdk = 26; targetSdk = 35; versionCode = 1; versionName = "0.1.0-preview" }
 compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
 buildFeatures { compose = true }
 kotlinOptions { jvmTarget = "17" }
}
dependencies {
 val bom = platform("androidx.compose:compose-bom:2026.03.01")
 implementation(bom)
 implementation("androidx.activity:activity-compose:1.11.0")
 implementation("androidx.compose.material3:material3")
 implementation("androidx.compose.foundation:foundation")
 implementation("androidx.compose.ui:ui")
 implementation("androidx.webkit:webkit:1.14.0")
 implementation("androidx.documentfile:documentfile:1.1.0")
 testImplementation("junit:junit:4.13.2")
}
