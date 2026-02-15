<template>
	<div class="p-4 sm:p-6">
		<div class="flex items-center justify-between mb-4">
			<h1 class="text-2xl font-semibold">Placement Test Submissions</h1>
			<Button variant="solid" size="sm" @click="refreshIframe">Refresh</Button>
		</div>
		<div class="border rounded-lg overflow-hidden bg-white shadow-sm">
			<iframe
				title="Placement Test Submission List"
				:src="listUrl"
				class="w-full h-[70vh]"
				ref="iframeRef"
				loading="lazy"
			></iframe>
		</div>
	</div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Button } from 'frappe-ui'

const iframeRef = ref(null)
const listUrl = computed(() => '/app/placement-test-submission?view=list')

const refreshIframe = () => {
	if (iframeRef.value) {
		const src = iframeRef.value.src
		iframeRef.value.src = src
	}
}
</script>
