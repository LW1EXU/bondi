plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}
android {
    namespace = "ar.com.bondi"
    compileSdk = 35
    defaultConfig {
        applicationId = "ar.com.bondi.preview"
        minSdk = 26
        targetSdk = 35
        versionCode = 3
        versionName = "0.3.0-alpha.1"
    }
    val previewKeystore = file(providers.environmentVariable("BONDI_KEYSTORE").orElse("../../.signing/preview.jks").get())
    val hasPreviewKeystore = previewKeystore.exists()
    signingConfigs {
        if (hasPreviewKeystore) {
            create("preview") {
                storeFile = previewKeystore
                storePassword = providers.environmentVariable("BONDI_STORE_PASSWORD").orNull
                keyAlias = "bondi-preview"
                keyPassword = providers.environmentVariable("BONDI_KEY_PASSWORD").orNull
            }
        }
    }
    buildTypes {
        getByName("release") {
            if (hasPreviewKeystore) {
                signingConfig = signingConfigs.getByName("preview")
            }
            isMinifyEnabled = false
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    buildFeatures { compose = true }
}
dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.04.01"))
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    debugImplementation("androidx.compose.ui:ui-tooling")
    testImplementation("junit:junit:4.13.2")
}
