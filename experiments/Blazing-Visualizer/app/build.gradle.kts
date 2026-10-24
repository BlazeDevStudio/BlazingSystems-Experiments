import java.util.Base64

plugins { id("com.android.application"); id("org.jetbrains.kotlin.android"); id("org.jetbrains.kotlin.plugin.compose"); id("org.jetbrains.kotlin.plugin.serialization") }
android {
 namespace="com.blazingsystems.visualizer"; compileSdk=36; buildToolsVersion="36.0.0"
 defaultConfig { applicationId="com.blazingsystems.visualizer"; minSdk=26; targetSdk=36; versionCode=5; versionName="1.0.0-preview.5"; testInstrumentationRunner="androidx.test.runner.AndroidJUnitRunner"; ndk { abiFilters+=listOf("arm64-v8a","x86_64") } }
 // Public preview identity, deliberately not a production signing credential.
 val previewStore = rootProject.file(".gradle/preview-signing.p12")
 previewStore.parentFile.mkdirs()
 previewStore.writeBytes(Base64.getMimeDecoder().decode(rootProject.file("config/preview-signing.p12.base64").readText()))
 signingConfigs.getByName("debug") { storeFile=previewStore; storeType="PKCS12"; storePassword="android"; keyAlias="blazing-preview"; keyPassword="android" }
 buildFeatures { compose=true; buildConfig=true }
 compileOptions { sourceCompatibility=JavaVersion.VERSION_17; targetCompatibility=JavaVersion.VERSION_17 }
 testOptions { unitTests.isIncludeAndroidResources=true }
 androidResources { noCompress+="tflite" }
 sourceSets.getByName("androidTest").assets.srcDir(rootProject.file("fixtures"))
 packaging { resources.excludes+=setOf("META-INF/AL2.0","META-INF/LGPL2.1") }
}
kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }
dependencies {
 implementation(platform("androidx.compose:compose-bom:2025.09.01"))
 implementation("androidx.activity:activity-compose:1.10.1")
 implementation("androidx.compose.ui:ui"); implementation("androidx.compose.material3:material3"); implementation("androidx.compose.material:material-icons-extended")
 implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.9.3")
 implementation("androidx.media3:media3-exoplayer:1.8.0"); implementation("androidx.media3:media3-session:1.8.0")
 implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0"); implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
 implementation("com.google.ai.edge.litert:litert:1.4.0")
 testImplementation("junit:junit:4.13.2"); testImplementation("org.robolectric:robolectric:4.16"); testImplementation("androidx.compose.ui:ui-test-junit4")
 testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.2")
 androidTestImplementation(platform("androidx.compose:compose-bom:2025.09.01")); androidTestImplementation("androidx.test.ext:junit:1.3.0"); androidTestImplementation("androidx.test:runner:1.7.0"); androidTestImplementation("androidx.compose.ui:ui-test-junit4")
 debugImplementation("androidx.compose.ui:ui-test-manifest")
}
